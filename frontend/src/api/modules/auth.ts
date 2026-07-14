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
  async logout() {
    try {
      await api.post<void>("/api/auth/logout");
    } finally {
      tokenStore.clear();
    }
  },
  me: () => api.get<AuthUser>("/api/auth/me"),
  forgotPassword: (email: string) =>
    api.post<{ ok: true }>("/api/auth/forgot-password", { email }, { auth: false }),
  resetPassword: (token: string, password: string) =>
    api.post<{ ok: true }>("/api/auth/reset-password", { token, password }, { auth: false }),
};
