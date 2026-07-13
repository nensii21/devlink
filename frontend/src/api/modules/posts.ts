import { api } from "../client";
import type { Flare } from "@/mocks/seed";

export const postsApi = {
  list: (query?: { page?: number; limit?: number }) => api.get<Flare[]>("/api/posts", { query }),
  create: (body: { content: string; image?: string; tags?: string[] }) =>
    api.post<Flare>("/api/posts", body),
  update: (id: string, body: Partial<Flare>) => api.put<Flare>(`/api/posts/${id}`, body),
  remove: (id: string) => api.delete<void>(`/api/posts/${id}`),
  like: (id: string) => api.post<{ likes: number }>(`/api/posts/${id}/like`),
  comment: (id: string, comment: string) =>
    api.post<unknown>(`/api/posts/${id}/comment`, { comment }),
};
