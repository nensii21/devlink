// Centralized fetch-based API client.
// - Reads base URL from VITE_API_BASE_URL
// - Attaches JWT access token
// - Auto-refreshes on 401 using refresh token
// - Standardized ApiError with status + payload
// - Simple retry with exponential backoff for network / 5xx

import { tokenStore } from "./tokens";

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

export const isBackendConfigured = (): boolean => API_BASE_URL.length > 0;

export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}
export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  retries?: number;
  timeout?: number;
  signal?: AbortSignal;
  query?: Record<string, string | number | boolean | undefined | null>;
  raw?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = path.startsWith("http")
    ? path
    : `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  if (!query) return url;
  const usp = new URLSearchParams();
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== null) usp.set(k, String(v));
  });
  const qs = usp.toString();
  return qs ? `${url}${url.includes("?") ? "&" : "?"}${qs}` : url;
}

// Single-flight refresh: parallel 401s share one refresh call.
let refreshInFlight: Promise<string | null> | null = null;

// Session Correlation ID for distributed tracing
let sessionCorrelationId =
  typeof sessionStorage !== "undefined" ? sessionStorage.getItem("x-correlation-id") : null;
if (!sessionCorrelationId) {
  sessionCorrelationId = `corr_${crypto.randomUUID ? crypto.randomUUID().replace(/-/g, "") : Math.random().toString(36).slice(2)}`;
  if (typeof sessionStorage !== "undefined") {
    sessionStorage.setItem("x-correlation-id", sessionCorrelationId);
  }
}

async function refreshAccessToken(): Promise<string | null> {
  if (!isBackendConfigured()) return null;
  const refresh = tokenStore.getRefresh();
  if (!refresh) return null;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const res = await fetch(buildUrl("/api/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        tokenStore.clear();
        return null;
      }
      const data = (await res.json()) as { access_token?: string; refresh_token?: string };
      if (!data.access_token) {
        tokenStore.clear();
        return null;
      }
      tokenStore.set(data.access_token, data.refresh_token ?? refresh);
      return data.access_token;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function coreFetch(path: string, opts: RequestOptions, attempt = 0): Promise<Response> {
  const {
    body,
    auth = true,
    query,
    retries = 2,
    timeout = 10000,
    signal,
    raw: _raw,
    headers,
    ...rest
  } = opts;
  void _raw;
  const finalHeaders = new Headers(headers);
  if (body !== undefined && !(body instanceof FormData)) {
    if (!finalHeaders.has("Content-Type")) finalHeaders.set("Content-Type", "application/json");
  }
  finalHeaders.set("Accept", finalHeaders.get("Accept") ?? "application/json");
  if (auth) {
    const token = tokenStore.getAccess();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  // Structured Logging Headers
  finalHeaders.set("X-Correlation-ID", sessionCorrelationId!);
  finalHeaders.set(
    "X-Request-ID",
    `req_${crypto.randomUUID ? crypto.randomUUID().replace(/-/g, "") : Math.random().toString(36).slice(2)}`,
  );

  const init: RequestInit = {
    ...rest,
    headers: finalHeaders,
    body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body),
  };

  let res: Response;

  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);

  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  try {
    res = await fetch(buildUrl(path, query), {
      ...init,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Request cancelled or timed out", 408, null);
    }

    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, 200 * 2 ** attempt));
      return coreFetch(path, opts, attempt + 1);
    }

    throw new ApiError(err instanceof Error ? err.message : "Network error", 0, null);
  }

  if (res.status === 503) {
    try {
      const payload = await res.clone().json();
      if (payload?.detail === "Maintenance Mode") {
        if (window.location.pathname !== "/maintenance") {
          window.location.href = "/maintenance";
        }
      }
    } catch (e) {
      // Not JSON, ignore
    }
  }

  if (res.status === 401 && auth && !path.includes("/auth/")) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      finalHeaders.set("Authorization", `Bearer ${newToken}`);
      res = await fetch(buildUrl(path, query), { ...init, headers: finalHeaders });
    }
  }

  if (res.status >= 500 && attempt < retries) {
    await new Promise((r) => setTimeout(r, 200 * 2 ** attempt));
    return coreFetch(path, opts, attempt + 1);
  }

  return res;
}

async function parseBody(res: Response): Promise<unknown> {
  const ct = res.headers.get("Content-Type") ?? "";
  if (res.status === 204) return null;
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const res = await coreFetch(path, opts);
  const payload = await parseBody(res);
  if (!res.ok) {
    const errorObj = typeof payload === "object" && payload && "error" in payload
      ? (payload as any).error
      : payload;

    const message =
      (errorObj && typeof errorObj === "object" && "message" in errorObj
        ? String(errorObj.message)
        : null) ??
      (typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : null) ??
      res.statusText ??
      `Request failed (${res.status})`;
    throw new ApiError(message, res.status, payload);
  }
  return payload as T;
}

export const api = {
  get: <T>(p: string, o?: RequestOptions) => request<T>(p, { ...o, method: "GET" }),
  post: <T>(p: string, body?: unknown, o?: RequestOptions) =>
    request<T>(p, { ...o, method: "POST", body }),
  put: <T>(p: string, body?: unknown, o?: RequestOptions) =>
    request<T>(p, { ...o, method: "PUT", body }),
  patch: <T>(p: string, body?: unknown, o?: RequestOptions) =>
    request<T>(p, { ...o, method: "PATCH", body }),
  delete: <T>(p: string, o?: RequestOptions) => request<T>(p, { ...o, method: "DELETE" }),
};
