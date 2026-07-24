import { api } from "../client";

export interface SearchResults {
  users?: unknown[];
  projects?: unknown[];
  posts?: unknown[];
  hackathons?: unknown[];
  organizations?: unknown[];
}

export const searchApi = {
  all: (q: string) => api.get<SearchResults>("/api/search", { query: { q } }),
};
