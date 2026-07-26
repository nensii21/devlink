import { api } from "../client";

export interface ProfileSummaryResponse {
  summary: string;
  user_id: string;
  user_name: string;
}

export const profileSummaryApi = {
  generate: (userId: string) =>
    api.post<ProfileSummaryResponse>("/api/profile-summary", {
      user_id: userId,
    }),
};
