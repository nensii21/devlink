import { api } from "../client";

export interface BookmarkResponse {
  id: string;
  user_id: string;
  project_id: string;
  created_at: string;
}

export interface BookmarkCheckResponse {
  bookmarked: boolean;
}

export interface BookmarkCountResponse {
  count: number;
}

export const bookmarksApi = {
  list: () => api.get<BookmarkResponse[]>("/bookmarks/"),

  check: (projectId: string) => api.get<BookmarkCheckResponse>(`/bookmarks/check/${projectId}`),

  count: (projectId: string) =>
    api.get<BookmarkCountResponse>(`/bookmarks/project/${projectId}/count`),

  add: (projectId: string) => api.post<BookmarkResponse>(`/bookmarks/project/${projectId}`),

  remove: (bookmarkId: string) => api.delete<void>(`/bookmarks/${bookmarkId}`),
};
