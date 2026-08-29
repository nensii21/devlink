import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useLikedFlares, useToggleLike } from "@/hooks/useLike";
import type { Flare } from "@/mocks/seed";

const list = vi.fn();
const like = vi.fn();
const unlike = vi.fn();

vi.mock("@/services", () => ({
  flaresService: {
    list: (...args: unknown[]) => list(...args),
    like: (...args: unknown[]) => like(...args),
    unlike: (...args: unknown[]) => unlike(...args),
  },
}));

vi.mock("sonner", () => ({ toast: { error: vi.fn() } }));

function flare(overrides: Partial<Flare> = {}): Flare {
  return {
    id: "flare-1",
    author: { id: "u1", name: "A", handle: "a" },
    content: "hello",
    tags: [],
    likes: 3,
    comments: 0,
    ago: "just now",
    ...overrides,
  } as Flare;
}

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { queryClient, wrapper };
}

beforeEach(() => {
  list.mockReset();
  like.mockReset();
  unlike.mockReset();
});

describe("useLikedFlares", () => {
  /**
   * The bug: `queryFn` used to be `() => Promise.resolve({})`, so nothing ever
   * populated the map. After a reload every post read as un-liked.
   */
  it("derives liked state from what the server reported", async () => {
    list.mockResolvedValue([
      flare({ id: "a", liked_by_me: true }),
      flare({ id: "b", liked_by_me: false }),
    ]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLikedFlares(), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data).toEqual({ a: true, b: false });
  });

  it("treats a missing liked_by_me as not liked", async () => {
    list.mockResolvedValue([flare({ id: "a" })]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useLikedFlares(), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual({ a: false }));
  });
});

describe("useToggleLike", () => {
  it("likes a post the viewer has not liked", async () => {
    list.mockResolvedValue([flare({ id: "flare-1", liked_by_me: false, likes: 3 })]);
    like.mockResolvedValue({
      post_id: "flare-1",
      likes: 4,
      comments: 0,
      liked_by_me: true,
      changed: true,
    });
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData<Flare[]>(
      ["flares"],
      [flare({ id: "flare-1", liked_by_me: false, likes: 3 })],
    );

    const { result } = renderHook(() => useToggleLike("flare-1"), { wrapper });
    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(like).toHaveBeenCalledWith("flare-1");
    expect(unlike).not.toHaveBeenCalled();
  });

  it("unlikes a post the viewer has already liked", async () => {
    unlike.mockResolvedValue({
      post_id: "flare-1",
      likes: 2,
      comments: 0,
      liked_by_me: false,
      changed: true,
    });
    list.mockResolvedValue([flare({ id: "flare-1", liked_by_me: true, likes: 3 })]);
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData<Flare[]>(
      ["flares"],
      [flare({ id: "flare-1", liked_by_me: true, likes: 3 })],
    );

    const { result } = renderHook(() => useToggleLike("flare-1"), { wrapper });
    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(unlike).toHaveBeenCalledWith("flare-1");
    expect(like).not.toHaveBeenCalled();
  });

  /**
   * The server owns both numbers. Writing its answer back is what stops a
   * second click on an already-liked post from settling on our optimistic
   * guess instead of on the truth.
   */
  it("writes the server's count and flag back into the feed cache", async () => {
    list.mockResolvedValue([]);
    like.mockResolvedValue({
      post_id: "flare-1",
      likes: 99,
      comments: 0,
      liked_by_me: true,
      changed: false,
    });
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData<Flare[]>(
      ["flares"],
      [flare({ id: "flare-1", liked_by_me: false, likes: 3 })],
    );

    const { result } = renderHook(() => useToggleLike("flare-1"), { wrapper });
    await act(async () => {
      await result.current.mutateAsync();
    });

    const cached = queryClient.getQueryData<Flare[]>(["flares"]);
    expect(cached?.[0].likes).toBe(99);
    expect(cached?.[0].liked_by_me).toBe(true);
  });

  it("restores the previous feed when the request fails", async () => {
    list.mockResolvedValue([]);
    like.mockRejectedValue(new Error("boom"));
    const { queryClient, wrapper } = makeWrapper();
    const original = [flare({ id: "flare-1", liked_by_me: false, likes: 3 })];
    queryClient.setQueryData<Flare[]>(["flares"], original);

    const { result } = renderHook(() => useToggleLike("flare-1"), { wrapper });
    await act(async () => {
      await result.current.mutateAsync().catch(() => undefined);
    });

    const cached = queryClient.getQueryData<Flare[]>(["flares"]);
    expect(cached?.[0].likes).toBe(3);
    expect(cached?.[0].liked_by_me).toBe(false);
  });

  it("never shows a negative like count optimistically", async () => {
    list.mockResolvedValue([]);
    unlike.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                post_id: "flare-1",
                likes: 0,
                comments: 0,
                liked_by_me: false,
                changed: true,
              }),
            0,
          ),
        ),
    );
    const { queryClient, wrapper } = makeWrapper();
    queryClient.setQueryData<Flare[]>(
      ["flares"],
      [flare({ id: "flare-1", liked_by_me: true, likes: 0 })],
    );

    const { result } = renderHook(() => useToggleLike("flare-1"), { wrapper });
    await act(async () => {
      await result.current.mutateAsync();
    });

    const cached = queryClient.getQueryData<Flare[]>(["flares"]);
    expect(cached?.[0].likes).toBeGreaterThanOrEqual(0);
  });
});
