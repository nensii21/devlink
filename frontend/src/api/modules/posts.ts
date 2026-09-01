import { api } from "@/api/client";
import type { Flare, PostComment, PostEngagement } from "@/types";
import { analyzeSpam } from "@/lib/validation/spamDetection";

export const postsApi = {
  list: (query?: { page?: number; limit?: number }) => api.get<Flare[]>("/api/posts", { query }),
  drafts: (query?: { page?: number; limit?: number }) =>
    api.get<Flare[]>("/api/posts/drafts", { query }),
  create: async (body: {
    content: string;
    image?: string;
    media_urls?: string[];
    tags?: string[];
    status?: string;
    publish_at?: string;
    repository?: { id?: string; name: string; url?: string; stars?: number; language?: string };
    project?: { id: string; title: string; tech_stack?: string[] };
    poll?: { question: string; options: string[]; expires_in_days?: number };
  }) => {
    const spamCheck = analyzeSpam(body.content);
    if (spamCheck.isSpam) {
      throw new Error(`Post rejected by AI Spam Filter: ${spamCheck.reasons.join(". ")}`);
    }
    return api.post<Flare>("/api/posts", body);
  },

  update: (id: string, body: Partial<Flare & { status?: string; publish_at?: string }>) =>
    api.put<Flare>(`/api/posts/${id}`, body),

  remove: (id: string) => api.delete<void>(`/api/posts/${id}`),

  like: (id: string) => api.post<PostEngagement>(`/api/posts/${id}/like`),
  unlike: (id: string) => api.delete<PostEngagement>(`/api/posts/${id}/like`),

  comments: (id: string, query?: { page?: number; limit?: number }) =>
    api.get<PostComment[]>(`/api/posts/${id}/comments`, { query }),
  comment: async (id: string, comment: string) => {
    const spamCheck = analyzeSpam(comment);
    if (spamCheck.isSpam) {
      throw new Error(`Comment rejected by AI Spam Filter: ${spamCheck.reasons.join(". ")}`);
    }
    return api.post<PostComment>(`/api/posts/${id}/comment`, { comment });
  },
  removeComment: (postId: string, commentId: string) =>
    api.delete<void>(`/api/posts/${postId}/comment/${commentId}`),
};
