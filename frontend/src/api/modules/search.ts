import { api } from "../client";

// ---------------------------------------------------------------------
// Search categories
// ---------------------------------------------------------------------

export type SearchCategory = "developers" | "projects" | "organizations" | "skills" | "tags";

export const SEARCH_CATEGORIES: readonly SearchCategory[] = [
  "developers",
  "projects",
  "organizations",
  "skills",
  "tags",
] as const;

// ---------------------------------------------------------------------
// Search History models
// ---------------------------------------------------------------------

export interface SearchHistoryItem {
  id: string;
  query: string;
  category?: SearchCategory | "all";
  timestamp: number;
}

const STORAGE_KEY = "devlink_recent_searches";
const MAX_HISTORY_ITEMS = 10;

// ---------------------------------------------------------------------
// Suggestion (lightweight autocomplete) models
// ---------------------------------------------------------------------

export interface SearchSuggestionUser {
  id: string;
  name: string;
  username: string;
  role?: string;
  profile_image?: string;
  verified?: boolean;
}

export interface SearchSuggestionProject {
  id: string;
  title: string;
  icon?: string;
  tagline?: string;
}

export interface SearchSuggestionOrganization {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  organization_type?: string;
  verified: boolean;
}

export interface SearchSuggestionSkill {
  id: string;
  name: string;
  category?: string;
}

export interface SearchSuggestionTag {
  name: string;
  project_count: number;
}

export interface SearchAutocompleteResponse {
  users: SearchSuggestionUser[];
  projects: SearchSuggestionProject[];
  organizations: SearchSuggestionOrganization[];
  skills: SearchSuggestionSkill[];
  tags: SearchSuggestionTag[];
}

// ---------------------------------------------------------------------
// Full search result models
// ---------------------------------------------------------------------

export interface SearchResultUser {
  id: string;
  name: string;
  username: string;
  role?: string;
  headline?: string;
  profile_image?: string;
  location?: string;
  verified?: boolean;
}

export interface SearchResultProject {
  id: string;
  title: string;
  slug: string;
  tagline?: string;
  description: string;
  logo_url?: string;
  stage?: string;
  stars: number;
  tags: string[];
}

export interface SearchResultOrganization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  organization_type?: string;
  location?: string;
  members_count: number;
  verified: boolean;
  hiring: boolean;
}

export interface SearchResultSkill {
  id: string;
  name: string;
  slug: string;
  category?: string;
  description?: string;
}

export interface SearchResultTag {
  name: string;
  project_count: number;
}

export interface SearchCounts {
  developers: number;
  projects: number;
  organizations: number;
  skills: number;
  tags: number;
  total: number;
}

export interface SearchResponse {
  query: string;
  category?: string | null;
  page: number;
  limit: number;
  counts: SearchCounts;
  users: SearchResultUser[];
  projects: SearchResultProject[];
  organizations: SearchResultOrganization[];
  skills: SearchResultSkill[];
  tags: SearchResultTag[];
}

// Legacy alias kept for backwards-compatibility with existing callers.
export interface SearchResults {
  users?: unknown[];
  projects?: unknown[];
  posts?: unknown[];
  hackathons?: unknown[];
  organizations?: unknown[];
}

// ---------------------------------------------------------------------
// Local Search History Utility Helpers
// ---------------------------------------------------------------------

export const searchHistoryStorage = {
  get: (): SearchHistoryItem[] => {
    if (typeof window === "undefined") return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },

  add: (query: string, category?: SearchCategory | "all"): SearchHistoryItem[] => {
    const trimmed = query.trim();
    if (!trimmed) return searchHistoryStorage.get();

    const current = searchHistoryStorage.get();
    const filtered = current.filter((item) => item.query.toLowerCase() !== trimmed.toLowerCase());

    const newItem: SearchHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      query: trimmed,
      category: category || "all",
      timestamp: Date.now(),
    };

    const updated = [newItem, ...filtered].slice(0, MAX_HISTORY_ITEMS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Ignore write errors (quota/incognito)
    }
    return updated;
  },

  remove: (id: string): SearchHistoryItem[] => {
    const current = searchHistoryStorage.get();
    const updated = current.filter((item) => item.id !== id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Ignore write errors
    }
    return updated;
  },

  clear: (): void => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore clear errors
    }
  },
};

// ---------------------------------------------------------------------
// API
// ---------------------------------------------------------------------

export interface SearchQuery {
  q: string;
  category?: SearchCategory;
  page?: number;
  limit?: number;
}

export const searchApi = {
  /** Full paginated search across all categories. */
  all: (params: SearchQuery) =>
    api.get<SearchResponse>("/api/search", {
      query: {
        q: params.q,
        category: params.category,
        page: params.page,
        limit: params.limit,
      },
    }),
  /** Lightweight per-category autocomplete payload. */
  autocomplete: (q: string) =>
    api.get<SearchAutocompleteResponse>("/api/search/autocomplete", { query: { q } }),
  /** Flat list of suggestion strings for keyboard-navigable dropdowns. */
  suggestions: (q: string, limit = 8) =>
    api.get<string[]>("/api/search/suggestions", { query: { q, limit } }),
  /** Optional API endpoint for backend-persisted search history */
  getHistory: () => api.get<SearchHistoryItem[]>("/api/search/history"),
  clearHistory: () => api.delete<{ success: boolean }>("/api/search/history"),
};
