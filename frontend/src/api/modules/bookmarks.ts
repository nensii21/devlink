import { api } from "../client";

export type BookmarkTargetType = "project" | "flare";

export interface BookmarkResponse {
  id: string;
  user_id: string;
  target_type: BookmarkTargetType;
  target_id: string;
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

  check: (targetType: BookmarkTargetType, targetId: string) =>
    api.get<BookmarkCheckResponse>(`/bookmarks/check/${targetType}/${targetId}`),

  count: (targetType: BookmarkTargetType, targetId: string) =>
    api.get<BookmarkCountResponse>(`/bookmarks/${targetType}/${targetId}/count`),

  add: (targetType: BookmarkTargetType, targetId: string) =>
    api.post<BookmarkResponse>(`/bookmarks/${targetType}/${targetId}`),

  remove: (bookmarkId: string) => api.delete<void>(`/bookmarks/${bookmarkId}`),
};
