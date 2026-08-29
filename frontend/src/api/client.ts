// Centralized fetch-based API client.
// - Reads base URL from VITE_API_BASE_URL
// - Attaches JWT access token
// - Auto-refreshes on 401 using refresh token
// - Standardized ApiError with status + payload
// - Retry with exponential backoff, but only for requests that are safe to
//   replay. See `isRetryableRequest` below.

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
  /**
   * Force the retry decision instead of inferring it from the method.
   *
   * Set this to `true` on a POST only when the endpoint is genuinely safe to
   * replay — either it is naturally idempotent server-side, or you are also
   * passing an `Idempotency-Key` header so the server can collapse duplicates.
   * Set it to `false` to opt a GET out of retrying.
   */
  idempotent?: boolean;
}

/**
 * Methods that RFC 9110 defines as idempotent: sending the same request twice
 * has the same effect on the server as sending it once. These are the only
 * ones we replay without being asked to.
 *
 * POST and PATCH are deliberately absent. A POST that times out on the way
 * back has very likely already been applied, and the client has no way to tell
 * that apart from a request that never arrived — replaying it is how you end
 * up with three applications to the same flare.
 */
const IDEMPOTENT_METHODS = new Set(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]);

/** Statuses worth a second attempt, assuming the request itself is replayable. */
const RETRYABLE_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);

/** Longest we will wait on a server-provided `Retry-After` before giving up on it. */
const MAX_RETRY_AFTER_MS = 20_000;

function isRetryableRequest(method: string, opts: RequestOptions): boolean {
  if (opts.idempotent !== undefined) return opts.idempotent;
  return IDEMPOTENT_METHODS.has(method.toUpperCase());
}

/**
 * `Retry-After` in milliseconds, or `null` when the header is absent or
 * unusable. The header comes in two forms — delta-seconds and an HTTP-date —
 * and servers send both.
 */
export function parseRetryAfter(header: string | null, now: number = Date.now()): number | null {
  if (!header) return null;

  const trimmed = header.trim();
  if (trimmed === "") return null;

  // Delta-seconds. Guard against the negative and non-finite cases rather than
  // trusting the header to be well formed.
  if (/^\d+$/.test(trimmed)) {
    const seconds = Number(trimmed);
    if (!Number.isFinite(seconds)) return null;
    return Math.min(seconds * 1000, MAX_RETRY_AFTER_MS);
  }

  // A header that is numeric but did not match above is a malformed
  // delta-seconds, not a date. Without this guard `Date.parse("-5")` reads it
  // as a year and we would wait until the year 5 BC — that is, not at all.
  if (/^[+-]?\d*\.?\d+$/.test(trimmed)) return null;

  const date = Date.parse(trimmed);
  if (Number.isNaN(date)) return null;

  const delta = date - now;
  if (delta <= 0) return 0;
  return Math.min(delta, MAX_RETRY_AFTER_MS);
}

/**
 * Exponential backoff with full jitter.
 *
 * Without the jitter every open tab that hit the same 503 retries at exactly
 * the same moment, which is precisely the load pattern a struggling API does
 * not need. Full jitter spreads them across the whole window.
 */
export function backoffDelay(attempt: number, base = 200): number {
  const ceiling = Math.min(base * 2 ** attempt, 8000);
  return Math.round(Math.random() * ceiling);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

/**
 * Send the request once, with its own timeout and linked to the caller's
 * abort signal.
 *
 * Split out from the retry loop so that every attempt — including the replay
 * after a token refresh — goes through the same timeout and cancellation
 * plumbing. Previously the post-refresh replay was a bare `fetch` with no
 * signal at all, so it could hang indefinitely and ignored cancellation.
 */
async function sendOnce(
  url: string,
  init: RequestInit,
  timeout: number,
  signal: AbortSignal | undefined,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // If the caller already gave up before we got here, do not open a socket.
  if (signal?.aborted) {
    clearTimeout(timeoutId);
    throw new ApiError("Request cancelled or timed out", 408, null);
  }

  const forwardAbort = () => controller.abort();
  signal?.addEventListener("abort", forwardAbort, { once: true });

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
    // Retries reuse the caller's signal, so the listener has to come off or
    // each attempt leaves one behind for the lifetime of the signal.
    signal?.removeEventListener("abort", forwardAbort);
  }
}

/** Send the browser to the maintenance page, if we are in a browser at all. */
function redirectToMaintenance(): void {
  // This client also runs during SSR, where `window` does not exist. Reading
  // `window.location` unguarded turned a maintenance response into a 500.
  if (typeof window === "undefined") return;
  if (window.location.pathname !== "/maintenance") {
    window.location.href = "/maintenance";
  }
}

async function coreFetch(path: string, opts: RequestOptions): Promise<Response> {
  const {
    body,
    auth = true,
    query,
    retries = 2,
    timeout = 10000,
    signal,
    raw: _raw,
    idempotent: _idempotent,
    headers,
    ...rest
  } = opts;
  void _raw;
  void _idempotent;

  const method = (rest.method ?? "GET").toUpperCase();
  const canRetry = isRetryableRequest(method, opts);
  const maxAttempts = canRetry ? retries + 1 : 1;

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

  const serialisedBody =
    body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body);

  const url = buildUrl(path, query);

  let lastNetworkError: unknown = null;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    // Rebuilt per attempt so a token refreshed mid-flight is picked up, and so
    // the request id is unique per attempt (the correlation id is not, on
    // purpose — that is what ties the attempts together in the logs).
    const init: RequestInit = { ...rest, headers: finalHeaders, body: serialisedBody };

    let res: Response;
    try {
      res = await sendOnce(url, init, timeout, signal);
    } catch (err) {
      if (err instanceof ApiError) throw err;

      if (err instanceof DOMException && err.name === "AbortError") {
        // A timeout is indistinguishable from "the server is still working on
        // it", so this is exactly the case a non-idempotent replay must not
        // take. `canRetry` already decided that for us.
        if (signal?.aborted || attempt === maxAttempts - 1) {
          throw new ApiError("Request cancelled or timed out", 408, null);
        }
        lastNetworkError = err;
        await sleep(backoffDelay(attempt));
        continue;
      }

      lastNetworkError = err;
      if (attempt === maxAttempts - 1) {
        throw new ApiError(err instanceof Error ? err.message : "Network error", 0, null);
      }
      await sleep(backoffDelay(attempt));
      continue;
    }

    if (res.status === 503) {
      try {
        const payload = await res.clone().json();
        if (payload?.detail === "Maintenance Mode") {
          redirectToMaintenance();
        }
      } catch {
        // Not JSON, ignore.
      }
    }

    if (res.status === 401 && auth && !path.includes("/auth/")) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        finalHeaders.set("Authorization", `Bearer ${newToken}`);
        try {
          // A 401 means the server rejected the request before acting on it,
          // so replaying it is safe regardless of method.
          res = await sendOnce(url, { ...init, headers: finalHeaders }, timeout, signal);
        } catch (err) {
          // This replay is outside the retry loop, so nothing below would
          // convert a raw fetch rejection into an ApiError. Callers catch
          // ApiError; letting a bare TypeError through here would slip past
          // every one of them.
          if (err instanceof ApiError) throw err;
          if (err instanceof DOMException && err.name === "AbortError") {
            throw new ApiError("Request cancelled or timed out", 408, null);
          }
          throw new ApiError(err instanceof Error ? err.message : "Network error", 0, null);
        }
      }
    }

    if (RETRYABLE_STATUSES.has(res.status) && attempt < maxAttempts - 1) {
      const retryAfter = parseRetryAfter(res.headers.get("Retry-After"));
      await sleep(retryAfter ?? backoffDelay(attempt));
      continue;
    }

    return res;
  }

  // Only reachable when every attempt failed at the network layer.
  throw new ApiError(
    lastNetworkError instanceof Error ? lastNetworkError.message : "Network error",
    0,
    null,
  );
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
    const message =
      (typeof payload === "object" &&
      payload &&
      "error" in payload &&
      typeof (payload as any).error === "object" &&
      (payload as any).error?.message
        ? String((payload as any).error.message)
        : null) ??
      (typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : null) ??
      (typeof payload === "object" && payload && "message" in payload
        ? String((payload as { message: unknown }).message)
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
