import { useCallback, useEffect, useRef, useState } from "react";

export interface UseIntersectionObserverOptions {
  /** Scroll container to measure against. `null` (default) means the viewport. */
  root?: Element | null;
  /** Margin grown around the root before intersection is reported. */
  rootMargin?: string;
  /** How much of the target must be visible. */
  threshold?: number | number[];
  /** Stop observing after the handler fires once. */
  once?: boolean;
}

const DEFAULT_ROOT_MARGIN = "200px";

/**
 * Call `onIntersect` when an element scrolls into view.
 *
 * Returns a ref callback: attach it to a sentinel element, usually an empty
 * div at the bottom of a list.
 *
 * Two things this is careful about, both of which caused real trouble in the
 * activity feed:
 *
 * **The handler lives in a ref.** If it were an observer dependency, every
 * change to its identity would tear the observer down and build a new one —
 * and `IntersectionObserver` fires its callback immediately on `observe()` for
 * an element that is already in view. With a handler whose identity changes
 * when a fetch starts and again when it finishes, that is a loop: fetch,
 * rebuild, fire, fetch. The feed pulled every page it had without the user
 * scrolling at all.
 *
 * **It only fires on a false → true transition.** While a sentinel stays in
 * view the browser reports `isIntersecting: true` again on any change to the
 * intersection ratio, so scrolling slowly inside `rootMargin` would otherwise
 * fire repeatedly.
 */
export function useIntersectionObserver(
  onIntersect: () => void,
  enabled: boolean,
  options: UseIntersectionObserverOptions = {},
): (node: Element | null) => void {
  const { root = null, rootMargin = DEFAULT_ROOT_MARGIN, threshold, once = false } = options;

  // The node lives in state rather than a ref so that attaching it re-runs the
  // effect below. One effect owning the observer's whole lifecycle is what
  // keeps a node from being observed twice, which is its own initial-report
  // double-fire.
  const [node, setNode] = useState<Element | null>(null);

  // The latest handler, without making it an observer dependency.
  const onIntersectRef = useRef(onIntersect);
  onIntersectRef.current = onIntersect;

  // Whether the sentinel was intersecting the last time we heard about it, so
  // the handler can fire on the edge rather than on every report.
  const wasIntersectingRef = useRef(false);

  // Set once `once` has fired, so a later re-observe does not fire again.
  const doneRef = useRef(false);

  // `threshold` is very often passed as an inline array. Serialising it stops a
  // fresh `[0.5]` on every render from counting as a change.
  const thresholdKey = JSON.stringify(threshold ?? null);

  useEffect(() => {
    if (!enabled || !node || doneRef.current) return;

    // Absent during SSR, and absent from jsdom, which is why anything using
    // this hook previously threw in tests.
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        // There is only ever one target per observer here, but the callback is
        // handed a batch and the last entry is the current state.
        const entry = entries[entries.length - 1];
        if (!entry) return;

        const isIntersecting = entry.isIntersecting;
        const wasIntersecting = wasIntersectingRef.current;
        wasIntersectingRef.current = isIntersecting;

        if (!isIntersecting || wasIntersecting || doneRef.current) return;

        if (once) {
          doneRef.current = true;
          observer.disconnect();
        }

        onIntersectRef.current();
      },
      {
        root,
        rootMargin,
        ...(threshold === undefined ? {} : { threshold }),
      },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
      // The next observer starts from a clean slate, so a sentinel that is
      // still in view is an edge again rather than a repeat.
      wasIntersectingRef.current = false;
    };
    // thresholdKey stands in for threshold, which may be a fresh array each render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node, enabled, root, rootMargin, thresholdKey, once]);

  // A stable identity, so React does not call it with null and then the node
  // again on every re-render. `setNode` bails out when handed the same node.
  return useCallback((next: Element | null) => setNode(next), []);
}
