import { api } from "../client";
import type { ApplicationResponse } from "@/lib/api";

export interface ApplicationPrefillData {
  user_id: string;
  full_name: string;
  username: string;
  headline?: string;
  skills: string[];
  github_url?: string;
  portfolio_url?: string;
  resume_url?: string;
  role?: string;
  suggested_cover_letter?: string;
}

export interface OneClickApplyPayload {
  project_id: string;
  flare_id?: string;
  selected_role?: string;
  cover_letter?: string;
  resume_url?: string;
  portfolio_url?: string;
  github_url?: string;
  auto_use_profile?: boolean;
}

export const applicationsApi = {
  getPrefill: async (): Promise<ApplicationPrefillData> => {
    return api.get<ApplicationPrefillData>("/api/applications/prefill");
  },

  oneClickApply: async (payload: OneClickApplyPayload): Promise<ApplicationResponse> => {
    return api.post<ApplicationResponse>("/api/applications/one-click", payload);
  },

  withdraw: async (applicationId: string): Promise<ApplicationResponse> => {
    return api.post<ApplicationResponse>(`/api/applications/${applicationId}/withdraw`);
  },

  getMyApplications: async (): Promise<ApplicationResponse[]> => {
    return api.get<ApplicationResponse[]>("/api/applications/me");
  },
};
