// JWT access + refresh token storage.
// Access token kept in-memory (safer against XSS); refresh in localStorage
// so sessions survive reloads. Swap to httpOnly cookies when backend supports.

const ACCESS_KEY = "devlink.access";
const REFRESH_KEY = "devlink.refresh";

let accessToken: string | null = null;

type Listener = (token: string | null) => void;
const listeners = new Set<Listener>();

export const tokenStore = {
  getAccess(): string | null {
    if (accessToken) return accessToken;
    if (typeof window === "undefined") return null;
    accessToken = window.sessionStorage.getItem(ACCESS_KEY);
    return accessToken;
  },
  getRefresh(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(REFRESH_KEY);
  },
  set(access: string | null, refresh?: string | null) {
    accessToken = access;
    if (typeof window !== "undefined") {
      if (access) window.sessionStorage.setItem(ACCESS_KEY, access);
      else window.sessionStorage.removeItem(ACCESS_KEY);
      if (refresh !== undefined) {
        if (refresh) window.localStorage.setItem(REFRESH_KEY, refresh);
        else window.localStorage.removeItem(REFRESH_KEY);
      }
    }
    listeners.forEach((l) => l(access));
  },
  clear() {
    this.set(null, null);
  },
  subscribe(l: Listener) {
    listeners.add(l);
    return () => listeners.delete(l);
  },
};
