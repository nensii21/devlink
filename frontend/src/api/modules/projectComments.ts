import { api } from "../client";

export interface CommentAuthor {
  id: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  profile_image: string | null;
}

export interface ProjectComment {
  id: string;
  project_id: string;
  /** Null for a top-level comment. Replies are one level deep. */
  parent_id: string | null;
  /** `"[deleted]"` when `is_deleted` is true — the real text is never sent. */
  body: string;
  /** Null on a deleted comment, so the thread does not name who wrote it. */
  author: CommentAuthor | null;
  is_edited: boolean;
  edited_at: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCommentThread extends ProjectComment {
  replies: ProjectComment[];
  reply_count: number;
}

export interface ProjectCommentList {
  items: ProjectCommentThread[];
  /** Top-level comments only, so it lines up with the page size. */
  total: number;
  limit: number;
  offset: number;
}

export interface ListCommentsParams {
  limit?: number;
  offset?: number;
}

export interface CreateCommentPayload {
  body: string;
  /** Omit for a top-level comment. */
  parent_id?: string | null;
}

export interface UpdateCommentPayload {
  body: string;
}

const base = (projectId: string) => `/api/v1/projects/${projectId}/comments`;

export const projectCommentsApi = {
  /** Top-level comments, newest first, each with its replies. */
  list(
    projectId: string,
    params: ListCommentsParams = {},
    signal?: AbortSignal,
  ): Promise<ProjectCommentList> {
    return api.get<ProjectCommentList>(base(projectId), {
      query: { limit: params.limit, offset: params.offset },
      signal,
    });
  },

  /** Live comments including replies — the number for a "12 comments" badge. */
  count(projectId: string, signal?: AbortSignal): Promise<{ count: number }> {
    return api.get<{ count: number }>(`${base(projectId)}/count`, { signal });
  },

  create(projectId: string, payload: CreateCommentPayload): Promise<ProjectComment> {
    // Send parent_id explicitly rather than omitting it, so the request body
    // has the same shape for a comment and a reply.
    return api.post<ProjectComment>(base(projectId), {
      body: payload.body,
      parent_id: payload.parent_id ?? null,
    });
  },

  update(
    projectId: string,
    commentId: string,
    payload: UpdateCommentPayload,
  ): Promise<ProjectComment> {
    return api.patch<ProjectComment>(`${base(projectId)}/${commentId}`, payload);
  },

  /**
   * Soft delete. The comment stays in the listing as a tombstone so replies
   * underneath it keep their context, so callers should refetch rather than
   * removing the row locally.
   */
  remove(projectId: string, commentId: string): Promise<void> {
    return api.delete<void>(`${base(projectId)}/${commentId}`);
  },
};
