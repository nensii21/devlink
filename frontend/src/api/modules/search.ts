import { api } from "../client";

export interface SearchResults {
  users?: unknown[];
  projects?: unknown[];
  posts?: unknown[];
  hackathons?: unknown[];
}

export interface SearchSuggestionUser {
  id: string;
  name: string;
  username: string;
  role?: string;
  profile_image?: string;
}

export interface SearchSuggestionProject {
  id: string;
  title: string;
  icon?: string;
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

export const searchApi = {
  all: (q: string) => api.get<SearchResults>("/api/search", { query: { q } }),
  autocomplete: (q: string) => api.get<SearchAutocompleteResponse>("/api/search/autocomplete", { query: { q } }),
};
