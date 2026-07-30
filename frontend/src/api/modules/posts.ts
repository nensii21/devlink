import { api } from "../client";
import type { Flare } from "@/mocks/seed";
import { analyzeSpam } from "@/lib/validation/spamDetection";

export const postsApi = {
  list: (query?: { page?: number; limit?: number }) => api.get<Flare[]>("/api/posts", { query }),
  create: async (body: { content: string; image?: string; tags?: string[] }) => {
    const spamCheck = analyzeSpam(body.content);
    if (spamCheck.isSpam) {
      throw new Error(`Post rejected by AI Spam Filter: ${spamCheck.reasons.join(". ")}`);
    }
    return api.post<Flare>("/api/posts", body);
  },
  update: (id: string, body: Partial<Flare>) => api.put<Flare>(`/api/posts/${id}`, body),
  remove: (id: string) => api.delete<void>(`/api/posts/${id}`),
  like: (id: string) => api.post<{ likes: number }>(`/api/posts/${id}/like`),
  unlike: (id: string) => api.delete<{ likes: number }>(`/api/posts/${id}/like`),
  comment: async (id: string, comment: string) => {
    const spamCheck = analyzeSpam(comment);
    if (spamCheck.isSpam) {
      throw new Error(`Comment rejected by AI Spam Filter: ${spamCheck.reasons.join(". ")}`);
    }
    return api.post<unknown>(`/api/posts/${id}/comment`, { comment });
  },
};
