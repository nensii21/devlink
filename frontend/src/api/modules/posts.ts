import { api } from "../client";
import type { Flare } from "@/mocks/seed";
import { analyzeSpam } from "@/lib/validation/spamDetection";

/** What the server reports after a like, unlike or comment. */
export interface PostEngagement {
  post_id: string;
  likes: number;
  comments: number;
  /** Whether the caller has liked the post, per the server. */
  liked_by_me: boolean;
  /** False when the request was a no-op — a second like, or an absent unlike. */
  changed: boolean;
}

export interface PostCommentAuthor {
  id: string;
  name: string;
  handle: string;
  avatar?: string | null;
  verified: boolean;
  premium: boolean;
}

export interface PostComment {
  id: string;
  post_id: string;
  author: PostCommentAuthor;
  content: string;
  ago: string;
  created_at: string;
  updated_at: string;
}

export const postsApi = {
  list: (query?: { page?: number; limit?: number }) => api.get<Flare[]>("/api/posts", { query }),
  drafts: (query?: { page?: number; limit?: number }) =>
    api.get<Flare[]>("/api/posts/drafts", { query }),
<<<<<< feature/account-deactivation-1306
  create: async (body: { content: string; image?: string; tags?: string[] }) => {

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
 main
    const spamCheck = analyzeSpam(body.content);
    if (spamCheck.isSpam) {
      throw new Error(`Post rejected by AI Spam Filter: ${spamCheck.reasons.join(". ")}`);
    }
    return api.post<Flare>("/api/posts", body);
  },
 feature/account-deactivation-1306
  update: (id: string, body: Partial<Flare>) => api.put<Flare>(`/api/posts/${id}`, body),

  update: (id: string, body: Partial<Flare & { status?: string; publish_at?: string }>) =>
    api.put<Flare>(`/api/posts/${id}`, body),
 main
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
    // The server stores the body now and returns the created comment, so the
    // spam check above is finally guarding something that gets persisted.
    return api.post<PostComment>(`/api/posts/${id}/comment`, { comment });
  },
  removeComment: (postId: string, commentId: string) =>
    api.delete<void>(`/api/posts/${postId}/comment/${commentId}`),
};
