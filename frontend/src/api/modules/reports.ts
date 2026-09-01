import { api } from "../client";

export interface UserReportPayload {
  reason: string;
  description?: string;
  post_id?: string;
}

export interface UserReportResponse {
  id: string;
  reporter_id: string;
  reported_id: string;
  post_id?: string;
  reason: string;
  description?: string;
  status: string;
  created_at: string;
}

export const reportsApi = {
  reportProfile: async (userId: string, payload: UserReportPayload): Promise<UserReportResponse> => {
    return api.post<UserReportResponse>(`/api/users/${userId}/report`, payload);
  },

  reportPost: async (postId: string, payload: UserReportPayload): Promise<UserReportResponse> => {
    return api.post<UserReportResponse>(`/api/posts/${postId}/report`, payload);
  },
};
