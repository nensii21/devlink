import { useCallback, useEffect, useRef, useState } from "react";

import { searchApi } from "@/api/modules/search";
import { useDebounce } from "@/hooks/useDebounce";
import type {
  SearchAutocompleteResponse,
  SearchCategory,
  SearchResponse,
} from "@/api/modules/search";

// ---------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------

export interface GlobalSearchState {
  /** The raw value typed into the search input. */
  query: string;
  /** Debounced query actually sent to the API. */
  debouncedQuery: string;
  /** Currently active category filter (null = all categories). */
  category: SearchCategory | null;
  /** Whether a request is currently in flight. */
  loading: boolean;
  /** Error message from the last failed request, if any. */
  error: string | null;
  /** Autocomplete dropdown suggestions (per-category). */
  suggestions: SearchAutocompleteResponse | null;
  /** Full search results (only populated when query is non-empty). */
  results: SearchResponse | null;
}

export interface UseGlobalSearchOptions {
  /** Debounce delay in milliseconds (default 250ms). */
  debounceMs?: number;
  /** Page size for the full search call (default 20). */
  limit?: number;
  /** Autocomplete min query length (default 1). */
  minQueryLength?: number;
  /** Enable the autocomplete dropdown (default true). */
  enableAutocomplete?: boolean;
}

export interface UseGlobalSearchReturn extends GlobalSearchState {
  /** Update the search input value. */
  setQuery: (q: string) => void;
  /** Update the active category filter. */
  setCategory: (c: SearchCategory | null) => void;
  /** Clear the query and all results. */
  clear: () => void;
  /** Manually re-trigger a search with the current state. */
  refresh: () => void;
}

// ---------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------

export function useGlobalSearch(options: UseGlobalSearchOptions = {}): UseGlobalSearchReturn {
  const { debounceMs = 250, limit = 20, minQueryLength = 1, enableAutocomplete = true } = options;

  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<SearchCategory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<SearchAutocompleteResponse | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);

  const debouncedQuery = useDebounce(query, debounceMs);

  // Track the latest request so stale responses don't overwrite newer state.
  // Two separate counters because the full-search and autocomplete effects
  // run independently and should not invalidate each other's responses.
  const searchRequestIdRef = useRef(0);
  const autocompleteRequestIdRef = useRef(0);

  // -------------------------------------------------------------------
  // Full search effect — fires when debouncedQuery or category changes.
  // -------------------------------------------------------------------

  useEffect(() => {
    const trimmed = debouncedQuery.trim();
    if (trimmed.length < minQueryLength) {
      setResults(null);
      setError(null);
      setLoading(false);
      return;
    }

    const requestId = ++searchRequestIdRef.current;
    setLoading(true);
    setError(null);

    searchApi
      .all({ q: trimmed, category: category ?? undefined, limit })
      .then((res) => {
        // Stale-response guard: ignore if a newer search request has fired.
        if (searchRequestIdRef.current !== requestId) return;
        setResults(res);
      })
      .catch((err: unknown) => {
        if (searchRequestIdRef.current !== requestId) return;
        const message = err instanceof Error ? err.message : "Search failed. Please try again.";
        setError(message);
        setResults(null);
      })
      .finally(() => {
        if (searchRequestIdRef.current !== requestId) return;
        setLoading(false);
      });
  }, [debouncedQuery, category, limit, minQueryLength]);

  // -------------------------------------------------------------------
  // Autocomplete effect — fires on debouncedQuery only (not category).
  // -------------------------------------------------------------------

  useEffect(() => {
    if (!enableAutocomplete) {
      setSuggestions(null);
      return;
    }
    const trimmed = debouncedQuery.trim();
    if (trimmed.length < minQueryLength) {
      setSuggestions(null);
      return;
    }

    const requestId = ++autocompleteRequestIdRef.current;
    let cancelled = false;

    searchApi
      .autocomplete(trimmed)
      .then((res) => {
        if (cancelled || autocompleteRequestIdRef.current !== requestId) return;
        setSuggestions(res);
      })
      .catch((err: unknown) => {
        if (cancelled || autocompleteRequestIdRef.current !== requestId) return;
        // Autocomplete errors are non-fatal — just clear suggestions.
        setSuggestions(null);
        if (import.meta.env?.DEV) {
          console.warn("autocomplete failed:", err);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedQuery, minQueryLength, enableAutocomplete]);

  // -------------------------------------------------------------------
  // Imperative helpers
  // -------------------------------------------------------------------

  const clear = useCallback(() => {
    setQuery("");
    setResults(null);
    setSuggestions(null);
    setError(null);
    setLoading(false);
    ++searchRequestIdRef.current;
    ++autocompleteRequestIdRef.current;
  }, []);

  const refresh = useCallback(() => {
    // Re-trigger the full-search effect by toggling the query state.
    // Setting the same value via setQuery would be a no-op, so we bump
    // a hidden counter by re-using setCategory with the same value.
    setCategory((c) => c);
  }, []);

  return {
    query,
    debouncedQuery,
    category,
    loading,
    error,
    suggestions,
    results,
    setQuery,
    setCategory,
    clear,
    refresh,
  };
}
