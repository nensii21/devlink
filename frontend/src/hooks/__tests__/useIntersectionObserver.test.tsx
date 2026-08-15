import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render } from "@testing-library/react";
import { useCallback, useState } from "react";

import { useIntersectionObserver } from "../useIntersectionObserver";

/**
 * A stand-in for the real thing, which jsdom does not implement.
 *
 * The important behaviour to reproduce is that a real `IntersectionObserver`
 * reports the target's current state as soon as `observe()` is called — that
 * initial report is what turned an observer rebuild into a fetch loop.
 */
class FakeIntersectionObserver implements IntersectionObserver {
  static instances: FakeIntersectionObserver[] = [];
  /** Whether a freshly observed target is treated as already in view. */
  static initiallyIntersecting = false;

  readonly root: Element | Document | null;
  readonly rootMargin: string;
  readonly thresholds: ReadonlyArray<number>;

  targets: Element[] = [];
  disconnected = false;

  private callback: IntersectionObserverCallback;

  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.callback = callback;
    this.root = (options?.root as Element | null) ?? null;
    this.rootMargin = options?.rootMargin ?? "0px";
    this.thresholds = options?.threshold === undefined ? [0] : [options.threshold].flat();
    FakeIntersectionObserver.instances.push(this);
  }

  observe(target: Element): void {
    this.targets.push(target);
    if (FakeIntersectionObserver.initiallyIntersecting) {
      this.emit(true);
    }
  }

  unobserve(target: Element): void {
    this.targets = this.targets.filter((t) => t !== target);
  }

  disconnect(): void {
    this.disconnected = true;
    this.targets = [];
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  /** Report an intersection state change to the hook. */
  emit(isIntersecting: boolean): void {
    if (this.disconnected) return;
    this.callback([{ isIntersecting, target: this.targets[0] } as IntersectionObserverEntry], this);
  }

  static get latest(): FakeIntersectionObserver {
    const observer = this.instances[this.instances.length - 1];
    if (!observer) throw new Error("no IntersectionObserver was constructed");
    return observer;
  }

  static get live(): FakeIntersectionObserver[] {
    return this.instances.filter((o) => !o.disconnected);
  }

  static reset(): void {
    this.instances = [];
    this.initiallyIntersecting = false;
  }
}

/** A component that mirrors how ActivityFeed wires the hook up. */
function Sentinel({
  onIntersect,
  enabled,
  options,
}: {
  onIntersect: () => void;
  enabled: boolean;
  options?: Parameters<typeof useIntersectionObserver>[2];
}) {
  const ref = useIntersectionObserver(onIntersect, enabled, options);
  return <div data-testid="sentinel" ref={ref} />;
}

describe("useIntersectionObserver", () => {
  beforeEach(() => {
    FakeIntersectionObserver.reset();
    vi.stubGlobal("IntersectionObserver", FakeIntersectionObserver);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("firing", () => {
    it("calls the handler when the sentinel comes into view", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled />);

      act(() => FakeIntersectionObserver.latest.emit(true));

      expect(onIntersect).toHaveBeenCalledTimes(1);
    });

    it("does not call the handler while the sentinel is out of view", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled />);

      act(() => FakeIntersectionObserver.latest.emit(false));

      expect(onIntersect).not.toHaveBeenCalled();
    });

    it("does not refire while the sentinel stays in view", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled />);

      const observer = FakeIntersectionObserver.latest;
      act(() => {
        // Scrolling slowly inside rootMargin reports isIntersecting again on
        // every ratio change.
        observer.emit(true);
        observer.emit(true);
        observer.emit(true);
      });

      expect(onIntersect).toHaveBeenCalledTimes(1);
    });

    it("fires again after the sentinel leaves and re-enters", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled />);

      const observer = FakeIntersectionObserver.latest;
      act(() => {
        observer.emit(true);
        observer.emit(false);
        observer.emit(true);
      });

      expect(onIntersect).toHaveBeenCalledTimes(2);
    });

    it("does nothing when disabled", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled={false} />);

      expect(FakeIntersectionObserver.instances).toHaveLength(0);
      expect(onIntersect).not.toHaveBeenCalled();
    });
  });

  describe("the fetch loop", () => {
    it("does not rebuild the observer when the handler identity changes", () => {
      const { rerender } = render(<Sentinel onIntersect={() => {}} enabled />);
      const before = FakeIntersectionObserver.instances.length;

      // A new inline arrow on every render, which is what happens whenever a
      // caller does not memoise, and what useCallback produces anyway once any
      // of its dependencies change.
      rerender(<Sentinel onIntersect={() => {}} enabled />);
      rerender(<Sentinel onIntersect={() => {}} enabled />);

      expect(FakeIntersectionObserver.instances).toHaveLength(before);
    });

    it("always calls the newest handler", () => {
      const first = vi.fn();
      const second = vi.fn();

      const { rerender } = render(<Sentinel onIntersect={first} enabled />);
      rerender(<Sentinel onIntersect={second} enabled />);

      act(() => FakeIntersectionObserver.latest.emit(true));

      expect(first).not.toHaveBeenCalled();
      expect(second).toHaveBeenCalledTimes(1);
    });

    it("does not loop when a fetch toggles enabled off and back on", () => {
      // This is the ActivityFeed bug end to end. The sentinel is already in
      // view, so every fresh observer reports an intersection immediately.
      FakeIntersectionObserver.initiallyIntersecting = true;

      function Feed() {
        const [pages, setPages] = useState(0);
        const [fetching, setFetching] = useState(false);

        const handleIntersect = useCallback(() => {
          setFetching(true);
          setPages((p) => p + 1);
          // Resolve the "fetch" straight away, which is the worst case.
          setFetching(false);
        }, []);

        const ref = useIntersectionObserver(handleIntersect, !fetching);

        return (
          <div>
            <span data-testid="pages">{pages}</span>
            <div ref={ref} />
          </div>
        );
      }

      const { getByTestId } = render(<Feed />);

      // Before the fix this ran away, pulling a page per rebuild until
      // hasNextPage went false. One page per scroll into view is correct.
      expect(getByTestId("pages").textContent).toBe("1");
    });

    it("fires once per visible sentinel even when the sentinel remounts", () => {
      // ActivityFeed used to render the sentinel only while
      // `!isFetchingNextPage`, so it was unmounted for the duration of every
      // fetch. A remounted node is a genuinely new node, so the hook cannot
      // dedupe it — the component has to keep it mounted. This pins the cost
      // of getting that wrong: one extra fire per remount, not zero.
      FakeIntersectionObserver.initiallyIntersecting = true;
      const onIntersect = vi.fn();

      function Remounting({ show }: { show: boolean }) {
        const ref = useIntersectionObserver(onIntersect, true);
        return show ? <div ref={ref} /> : null;
      }

      const { rerender } = render(<Remounting show />);
      expect(onIntersect).toHaveBeenCalledTimes(1);

      rerender(<Remounting show={false} />);
      rerender(<Remounting show />);

      expect(onIntersect).toHaveBeenCalledTimes(2);
      expect(FakeIntersectionObserver.live).toHaveLength(1);
    });

    it("does not refire when a re-render hands back the same node", () => {
      FakeIntersectionObserver.initiallyIntersecting = true;
      const onIntersect = vi.fn();

      const { rerender } = render(<Sentinel onIntersect={onIntersect} enabled />);
      rerender(<Sentinel onIntersect={onIntersect} enabled />);
      rerender(<Sentinel onIntersect={onIntersect} enabled />);

      expect(onIntersect).toHaveBeenCalledTimes(1);
    });
  });

  describe("options", () => {
    it("defaults to a 200px root margin", () => {
      render(<Sentinel onIntersect={vi.fn()} enabled />);

      expect(FakeIntersectionObserver.latest.rootMargin).toBe("200px");
    });

    it("accepts a custom root margin", () => {
      render(<Sentinel onIntersect={vi.fn()} enabled options={{ rootMargin: "50px" }} />);

      expect(FakeIntersectionObserver.latest.rootMargin).toBe("50px");
    });

    it("accepts a threshold", () => {
      render(<Sentinel onIntersect={vi.fn()} enabled options={{ threshold: 0.5 }} />);

      expect(FakeIntersectionObserver.latest.thresholds).toEqual([0.5]);
    });

    it("accepts a scroll container as the root", () => {
      const root = document.createElement("div");

      render(<Sentinel onIntersect={vi.fn()} enabled options={{ root }} />);

      expect(FakeIntersectionObserver.latest.root).toBe(root);
    });

    it("does not rebuild when an inline threshold array is recreated", () => {
      const { rerender } = render(
        <Sentinel onIntersect={vi.fn()} enabled options={{ threshold: [0, 0.5] }} />,
      );
      const before = FakeIntersectionObserver.instances.length;

      rerender(<Sentinel onIntersect={vi.fn()} enabled options={{ threshold: [0, 0.5] }} />);

      expect(FakeIntersectionObserver.instances).toHaveLength(before);
    });

    it("rebuilds when the root margin actually changes", () => {
      const { rerender } = render(
        <Sentinel onIntersect={vi.fn()} enabled options={{ rootMargin: "10px" }} />,
      );

      rerender(<Sentinel onIntersect={vi.fn()} enabled options={{ rootMargin: "80px" }} />);

      expect(FakeIntersectionObserver.latest.rootMargin).toBe("80px");
      expect(FakeIntersectionObserver.live).toHaveLength(1);
    });
  });

  describe("once", () => {
    it("fires a single time and stops observing", () => {
      const onIntersect = vi.fn();
      render(<Sentinel onIntersect={onIntersect} enabled options={{ once: true }} />);

      const observer = FakeIntersectionObserver.latest;
      act(() => observer.emit(true));

      expect(onIntersect).toHaveBeenCalledTimes(1);
      expect(observer.disconnected).toBe(true);
    });

    it("does not fire again after re-entering the viewport", () => {
      const onIntersect = vi.fn();
      const { rerender } = render(
        <Sentinel onIntersect={onIntersect} enabled options={{ once: true }} />,
      );

      act(() => FakeIntersectionObserver.latest.emit(true));
      rerender(<Sentinel onIntersect={onIntersect} enabled options={{ once: true }} />);

      expect(onIntersect).toHaveBeenCalledTimes(1);
      expect(FakeIntersectionObserver.live).toHaveLength(0);
    });
  });

  describe("teardown", () => {
    it("disconnects on unmount", () => {
      const { unmount } = render(<Sentinel onIntersect={vi.fn()} enabled />);
      const observer = FakeIntersectionObserver.latest;

      unmount();

      expect(observer.disconnected).toBe(true);
    });

    it("leaves no live observer behind when disabled after being enabled", () => {
      const { rerender } = render(<Sentinel onIntersect={vi.fn()} enabled />);

      rerender(<Sentinel onIntersect={vi.fn()} enabled={false} />);

      expect(FakeIntersectionObserver.live).toHaveLength(0);
    });

    it("never keeps more than one live observer across many re-renders", () => {
      const { rerender } = render(<Sentinel onIntersect={vi.fn()} enabled />);

      for (let i = 0; i < 10; i += 1) {
        rerender(<Sentinel onIntersect={vi.fn()} enabled={i % 2 === 0} />);
      }

      expect(FakeIntersectionObserver.live.length).toBeLessThanOrEqual(1);
    });

    it("re-observes when the hook is enabled again", () => {
      const onIntersect = vi.fn();
      const { rerender } = render(<Sentinel onIntersect={onIntersect} enabled={false} />);

      rerender(<Sentinel onIntersect={onIntersect} enabled />);
      act(() => FakeIntersectionObserver.latest.emit(true));

      expect(onIntersect).toHaveBeenCalledTimes(1);
    });
  });

  describe("environments without IntersectionObserver", () => {
    it("renders without throwing", () => {
      vi.unstubAllGlobals();
      // @ts-expect-error deliberately removing the global for this assertion
      vi.stubGlobal("IntersectionObserver", undefined);

      expect(() => render(<Sentinel onIntersect={vi.fn()} enabled />)).not.toThrow();
    });

    it("unmounts cleanly too", () => {
      vi.unstubAllGlobals();
      // @ts-expect-error deliberately removing the global for this assertion
      vi.stubGlobal("IntersectionObserver", undefined);

      const { unmount } = render(<Sentinel onIntersect={vi.fn()} enabled />);

      expect(() => unmount()).not.toThrow();
    });
  });
});
