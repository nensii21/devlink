import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

import { useGlobalSearch } from "@/hooks/useGlobalSearch";
import type { SearchAutocompleteResponse, SearchResponse } from "@/api/modules/search";

// ---------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------

vi.mock("@/api/modules/search", async () => {
  const actual =
    await vi.importActual<typeof import("@/api/modules/search")>("@/api/modules/search");
  return {
    ...actual,
    searchApi: {
      all: vi.fn(),
      autocomplete: vi.fn(),
      suggestions: vi.fn(),
    },
  };
});

// Import the mocked module so we can spy on its methods.
import { searchApi } from "@/api/modules/search";

function makeEmptyResponse(): SearchResponse {
  return {
    query: "",
    category: null,
    page: 1,
    limit: 20,
    counts: {
      developers: 0,
      projects: 0,
      organizations: 0,
      skills: 0,
      tags: 0,
      total: 0,
    },
    users: [],
    projects: [],
    organizations: [],
    skills: [],
    tags: [],
  };
}

function makeEmptyAutocomplete(): SearchAutocompleteResponse {
  return {
    users: [],
    projects: [],
    organizations: [],
    skills: [],
    tags: [],
  };
}

// ---------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  (searchApi.all as ReturnType<typeof vi.fn>).mockResolvedValue(makeEmptyResponse());
  (searchApi.autocomplete as ReturnType<typeof vi.fn>).mockResolvedValue(makeEmptyAutocomplete());
});

describe("useGlobalSearch", () => {
  it("starts idle with empty query and no results", () => {
    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    expect(result.current.query).toBe("");
    expect(result.current.debouncedQuery).toBe("");
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.results).toBeNull();
    expect(result.current.suggestions).toBeNull();
    expect(result.current.category).toBeNull();
  });

  it("does not fire API calls for empty / whitespace-only query", async () => {
    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("   ");
    });
    // Give React + the debounce a chance to flush.
    await new Promise((r) => setTimeout(r, 30));

    expect(searchApi.all).not.toHaveBeenCalled();
    expect(searchApi.autocomplete).not.toHaveBeenCalled();
  });

  it("debounces the query before hitting the API", async () => {
    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 80 }));

    await act(async () => {
      result.current.setQuery("react");
    });
    // Immediately after typing — no API call yet.
    expect(searchApi.all).not.toHaveBeenCalled();

    // Wait past the debounce window.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 150));
    });

    expect(searchApi.all).toHaveBeenCalledWith(expect.objectContaining({ q: "react", limit: 20 }));
  });

  it("calls the full search API with the active category filter", async () => {
    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setCategory("projects");
    });
    await act(async () => {
      result.current.setQuery("react");
    });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 30));
    });

    expect(searchApi.all).toHaveBeenCalledWith(
      expect.objectContaining({ q: "react", category: "projects", limit: 20 }),
    );
  });

  it("stores results from a successful search", async () => {
    const mockResponse: SearchResponse = {
      query: "react",
      category: null,
      page: 1,
      limit: 20,
      counts: {
        developers: 1,
        projects: 1,
        organizations: 0,
        skills: 0,
        tags: 0,
        total: 2,
      },
      users: [
        {
          id: "u1",
          name: "Alice React",
          username: "alice",
          role: "Frontend Dev",
        },
      ],
      projects: [
        {
          id: "p1",
          title: "Awesome React App",
          slug: "awesome-react-app",
          description: "A React app",
          stars: 10,
          tags: ["react"],
        },
      ],
      organizations: [],
      skills: [],
      tags: [],
    };
    (searchApi.all as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("react");
    });

    await waitFor(
      () => {
        expect(result.current.results).not.toBeNull();
      },
      { timeout: 2000 },
    );

    expect(result.current.results?.counts.total).toBe(2);
    expect(result.current.results?.users).toHaveLength(1);
    expect(result.current.results?.projects[0].title).toBe("Awesome React App");
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets an error message when the full search call rejects", async () => {
    (searchApi.all as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Network down"));

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("react");
    });

    await waitFor(
      () => {
        expect(result.current.error).toBe("Network down");
      },
      { timeout: 2000 },
    );
    expect(result.current.results).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("fetches autocomplete suggestions independently of the full search", async () => {
    const mockAutocomplete: SearchAutocompleteResponse = {
      users: [
        {
          id: "u1",
          name: "Alice",
          username: "alice",
        },
      ],
      projects: [],
      organizations: [],
      skills: [],
      tags: [],
    };
    (searchApi.autocomplete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockAutocomplete);

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("alice");
    });

    await waitFor(() => {
      expect(result.current.suggestions).not.toBeNull();
    });
    expect(result.current.suggestions?.users).toHaveLength(1);
    expect(result.current.suggestions?.users[0].username).toBe("alice");
  });

  it("autocomplete errors are non-fatal and clear suggestions", async () => {
    (searchApi.autocomplete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("timeout"),
    );

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("alice");
    });

    // The full-search error must NOT be set by an autocomplete failure.
    // Wait long enough for the rejected promise to settle.
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    await waitFor(() => {
      expect(result.current.suggestions).toBeNull();
    });
    expect(result.current.error).toBeNull();
  });

  it("clear() resets query, results, suggestions, and error", async () => {
    (searchApi.all as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("fail"));

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("react");
    });

    await waitFor(
      () => {
        expect(result.current.error).toBe("fail");
      },
      { timeout: 2000 },
    );

    act(() => {
      result.current.clear();
    });

    expect(result.current.query).toBe("");
    expect(result.current.results).toBeNull();
    expect(result.current.suggestions).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("ignores stale autocomplete responses when a newer query is typed", async () => {
    // First call resolves slowly with stale data, second call resolves quickly.
    let resolveFirst: (v: SearchAutocompleteResponse) => void = () => {};
    const firstPromise = new Promise<SearchAutocompleteResponse>((resolve) => {
      resolveFirst = resolve;
    });
    const secondResponse: SearchAutocompleteResponse = {
      users: [{ id: "u2", name: "Bob", username: "bob" }],
      projects: [],
      organizations: [],
      skills: [],
      tags: [],
    };
    (searchApi.autocomplete as ReturnType<typeof vi.fn>)
      .mockReturnValueOnce(firstPromise)
      .mockReturnValueOnce(Promise.resolve(secondResponse));

    const { result } = renderHook(() => useGlobalSearch({ debounceMs: 0 }));

    await act(async () => {
      result.current.setQuery("a");
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 20));
    });

    await act(async () => {
      result.current.setQuery("ab");
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 20));
    });

    // Resolve the stale (first) request last.
    await act(async () => {
      resolveFirst({
        users: [{ id: "stale", name: "Stale", username: "stale" }],
        projects: [],
        organizations: [],
        skills: [],
        tags: [],
      });
    });

    await waitFor(() => {
      expect(result.current.suggestions?.users[0].username).toBe("bob");
    });
  });

  it("can disable the autocomplete dropdown via options", async () => {
    const { result } = renderHook(() =>
      useGlobalSearch({ debounceMs: 0, enableAutocomplete: false }),
    );

    await act(async () => {
      result.current.setQuery("react");
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 30));
    });

    expect(searchApi.autocomplete).not.toHaveBeenCalled();
    expect(result.current.suggestions).toBeNull();
  });
});
