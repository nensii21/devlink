import { api } from "../client";

export interface UserSession {
  id: string;
  device_name?: string | null;
  device_type?: string | null;
  browser?: string | null;
  operating_system?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  is_revoked: boolean;
  created_at: string;
  last_used_at?: string | null;
  expires_at: string;
  is_current: boolean;
}

export interface RevokeSessionResponse {
  success: boolean;
  message: string;
  revoked_count: number;
}

export const sessionsApi = {
  getSessions: async (): Promise<UserSession[]> => {
    return api.get<UserSession[]>("/api/auth/sessions");
  },

  revokeSession: async (sessionId: string): Promise<RevokeSessionResponse> => {
    return api.delete<RevokeSessionResponse>(`/api/auth/sessions/${sessionId}`);
  },

  revokeOtherSessions: async (): Promise<RevokeSessionResponse> => {
    return api.post<RevokeSessionResponse>("/api/auth/sessions/revoke-others");
  },

  revokeAllSessions: async (): Promise<RevokeSessionResponse> => {
    return api.delete<RevokeSessionResponse>("/api/auth/sessions");
  },
};
