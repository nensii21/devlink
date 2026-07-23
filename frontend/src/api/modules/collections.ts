import { api } from "../client";

export interface BookmarkCollection {
  id: string;
  user_id: string;
  name: string;
  is_default: boolean;
  bookmark_count: number;
  created_at: string;
  updated_at: string;
}

export interface BookmarkCollectionWithBookmarks extends BookmarkCollection {
  bookmarks: Array<{
    id: string;
    user_id: string;
    project_id: string;
    created_at: string;
  }>;
}

export interface Bookmark {
  id: string;
  user_id: string;
  project_id: string;
  created_at: string;
}

export const collectionsApi = {
  list: () => api.get<BookmarkCollection[]>("/api/bookmark-collections"),

  get: (id: string) => api.get<BookmarkCollectionWithBookmarks>(`/api/bookmark-collections/${id}`),

  create: (name: string) => api.post<BookmarkCollection>("/api/bookmark-collections", { name }),

  rename: (id: string, name: string) =>
    api.patch<BookmarkCollection>(`/api/bookmark-collections/${id}`, {
      name,
    }),

  delete: (id: string) => api.delete<void>(`/api/bookmark-collections/${id}`),

  addBookmark: (collectionId: string, bookmarkId: string) =>
    api.post<{ success: boolean; bookmark_count: number }>(
      `/api/bookmark-collections/${collectionId}/bookmarks/${bookmarkId}`,
    ),

  removeBookmark: (collectionId: string, bookmarkId: string) =>
    api.delete<void>(`/api/bookmark-collections/${collectionId}/bookmarks/${bookmarkId}`),

  getBookmarkCollections: (bookmarkId: string) =>
    api.get<BookmarkCollection[]>(`/api/bookmark-collections/bookmark/${bookmarkId}/collections`),
};
