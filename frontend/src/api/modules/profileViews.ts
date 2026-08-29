import { api } from "../client";

export interface ProfileViewItem {
  id: string;
  viewer_id?: string;
  viewer_name: string;
  viewer_username: string;
  viewer_avatar?: string;
  viewed_at: string;
  visit_count: number;
  is_anonymous: boolean;
}

export interface PaginatedProfileViewsResponse {
  items: ProfileViewItem[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface ProfileViewPrivacyResponse {
  hide_profile_views: boolean;
}

export const profileViewsApi = {
  recordView: (userId: string) =>
    api.post<{ status: string; view_id?: string }>(`/api/profile-views/${userId}`),

  getHistory: (page: number = 1, size: number = 10) =>
    api.get<PaginatedProfileViewsResponse>(`/api/profile-views/history?page=${page}&size=${size}`),

  getPrivacy: () =>
    api.get<ProfileViewPrivacyResponse>("/api/profile-views/privacy"),

  updatePrivacy: (hideProfileViews: boolean) =>
    api.put<ProfileViewPrivacyResponse>("/api/profile-views/privacy", {
      hide_profile_views: hideProfileViews,
    }),
};
