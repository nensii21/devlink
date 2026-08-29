import { api } from "../client";

/**
 * The authenticated user as `/api/users/me` returns it.
 *
 * Deliberately wider than `AuthUser` in `modules/auth`: that one describes the
 * summary embedded in a login response, this one is the full profile row the
 * settings page edits. `handle` is the legacy spelling of `username` and is
 * still present on older rows.
 *
 * `version` is the optimistic-concurrency token. Send it back on a write and
 * the server answers 409 if the profile changed underneath you; drop it and
 * the last write silently wins.
 */
export interface CurrentUserProfile {
  id: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  handle?: string;
  email?: string;
  bio?: string;
  headline?: string;
  location?: string;
  website?: string;
  avatar?: string;
  profile_image?: string;
  version?: number;
}

export interface UserProfileUpdateData {
  first_name?: string;
  last_name?: string;
  username?: string;
  headline?: string;
  bio?: string;
  location?: string;
  website?: string;
  profile_image?: string;
  github_url?: string;
  linkedin_url?: string;
  twitter_url?: string;
  portfolio_url?: string;
  role?: string;
  experience_level?: string;
  company?: string;
  skills?: string[];
}

export const usersApi = {
  list: (query?: { page?: number; limit?: number; q?: string }) =>
    api.get<unknown[]>("/api/users", { query }),
  get: (id: string) => api.get<unknown>(`/api/users/${id}`),
  /**
   * The caller's own profile. Typed, so the settings page's reads of
   * `version` and the legacy `handle` are checked rather than `any` (#1315).
   */
  getMe: () => api.get<CurrentUserProfile>("/api/users/me"),
  getByUsername: (username: string) => api.get<any>(`/api/users/by-username/${username}`),
  update: (id: string, body: Record<string, unknown>) => api.put<unknown>(`/api/users/${id}`, body),
  updateProfile: (body: UserProfileUpdateData) => api.put<unknown>("/api/users/me", body),
  updateMe: (body: Record<string, unknown>) => api.put<unknown>("/api/users/me", body),
  getPrivacySettings: () => api.get<any>("/api/users/me/privacy"),
  updatePrivacySettings: (body: Record<string, any>) =>
    api.put<unknown>("/api/users/me/privacy", body),
  remove: (id: string) => api.delete<void>(`/api/users/${id}`),
  search: (q: string) => api.get<unknown[]>("/api/users/search", { query: { q } }),
  recommendations: () => api.get<unknown[]>("/api/users/recommendations"),
  follow: (id: string) => api.post<void>("/api/users/follow", { user_id: id }),
  unfollow: (id: string) => api.delete<void>("/api/users/unfollow", { query: { user_id: id } }),
  report: (id: string, data: { reason: string; description?: string }) =>
    api.post<unknown>(`/api/users/${id}/report`, data),
  completion: () =>
    api.get<{
      completion: number;
      missing: string[];
      completed_factors: string[];
      reward_unlocked: boolean;
      reward_badge?: string;
    }>("/api/users/me/completion"),
  getCollaborationStatus: () =>
    api.get<{ user_id: string; status: string }>("/api/users/me/collaboration-status"),
  setCollaborationStatus: (status: string) =>
    api.put<{ user_id: string; status: string }>("/api/users/me/collaboration-status", undefined, {
      query: { status_val: status },
    }),
};
