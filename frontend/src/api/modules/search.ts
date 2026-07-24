import { api } from "../client";

// ---------------------------------------------------------------------------
// Search result item shapes (mirror backend Pydantic response schemas)
// ---------------------------------------------------------------------------

export interface SearchUser {
  id: string;
  first_name: string;
  last_name: string;
  username: string;
  headline?: string | null;
  bio?: string | null;
  profile_image?: string | null;
  location?: string | null;
  role?: string | null;
  is_verified?: boolean;
}

export interface SearchProject {
  id: string;
  title: string;
  slug: string;
  tagline?: string | null;
  description: string;
  tech_stack?: string | null;
  stars: number;
  is_featured: boolean;
  logo_url?: string | null;
}

export interface SearchOrganization {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  logo_url?: string | null;
  location?: string | null;
  verified: boolean;
  members_count: number;
}

export interface SearchSkill {
  id: string;
  name: string;
  slug: string;
  category?: string | null;
  description?: string | null;
}

export interface SearchFlare {
  id: string;
  title: string;
  description: string;
  role: string;
  status: string;
  project_id: string;
  created_by: string;
}

export interface SearchResultGroups {
  users: SearchUser[];
  projects: SearchProject[];
  organizations: SearchOrganization[];
  skills: SearchSkill[];
  flares: SearchFlare[];
}

export interface SearchResponse {
  query: string;
  types: string[];
  total: number;
  results: SearchResultGroups;
}

// ---------------------------------------------------------------------------
// Autocomplete suggestion shapes (lightweight, for the Topbar typeahead)
// ---------------------------------------------------------------------------

export interface SearchSuggestionUser {
  id: string;
  name: string;
  username: string;
  role?: string | null;
  profile_image?: string | null;
}

export interface SearchSuggestionProject {
  id: string;
  title: string;
  icon?: string | null;
}

export interface SearchSuggestionSkill {
  id: string;
  name: string;
}

export interface SearchAutocompleteResponse {
  users: SearchSuggestionUser[];
  projects: SearchSuggestionProject[];
  skills: SearchSuggestionSkill[];
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

export const searchApi = {
  all: (q: string, types?: string[], limit?: number) =>
    api.get<SearchResponse>("/api/search", {
      query: { q, types: types?.join(","), limit },
    }),
  autocomplete: (q: string) =>
    api.get<SearchAutocompleteResponse>("/api/search/autocomplete", { query: { q } }),
};
