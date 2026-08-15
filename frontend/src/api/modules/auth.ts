import { api } from "../client";
import { tokenStore } from "../tokens";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}
export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar?: string;
  profile_image?: string;
  is_pro?: boolean;
}
export interface AuthResponse extends AuthTokens {
  user: AuthUser;
}

export const authApi = {
  async register(input: { email: string; username: string; password: string; full_name?: string }) {
    const res = await api.post<AuthResponse>("/api/auth/register", input, { auth: false });
    tokenStore.set(res.access_token, res.refresh_token);
    return res;
  },
  async login(input: { email: string; password: string }) {
    const res = await api.post<AuthResponse>("/api/auth/login", input, { auth: false });
    tokenStore.set(res.access_token, res.refresh_token);
    return res;
  },
  async githubLogin(code: string, state: string) {
    const res = await api.post<AuthResponse>("/api/auth/github", { code, state }, { auth: false });
    tokenStore.set(res.access_token, res.refresh_token);
    return res;
  },
  async linkedinLogin(code: string, state: string) {
    const res = await api.post<AuthResponse>(
      "/api/auth/linkedin",
      { code, state },
      { auth: false },
    );
    tokenStore.set(res.access_token, res.refresh_token);
    return res;
  },
  oauthAuthorize: (provider: "github" | "linkedin") =>
    api.get<{ state: string }>(`/api/auth/${provider}/authorize`, { auth: false }),
  async logout() {
    try {
      await api.post<void>("/api/auth/logout", { refresh_token: tokenStore.getRefresh() });
    } finally {
      tokenStore.clear();
    }
  },
  me: () => api.get<AuthUser>("/api/auth/me"),
  forgotPassword: (email: string) =>
    api.post<{ ok: true }>("/api/auth/forgot-password", { email }, { auth: false }),
  resetPassword: (token: string, password: string) =>
    api.post<{ ok: true }>(
      "/api/auth/reset-password",
      { token, new_password: password },
      { auth: false },
    ),
};
