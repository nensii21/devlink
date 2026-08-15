import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, backoffDelay, parseRetryAfter, request } from "../client";
import { tokenStore } from "../tokens";

/** A JSON response, the shape the client actually parses. */
function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  // 204 and 304 are not allowed to carry a body.
  const hasBody = status !== 204 && status !== 304;
  return new Response(hasBody ? JSON.stringify(body) : null, {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

/** The error `fetch` throws when the connection drops. */
function networkError() {
  return new TypeError("Failed to fetch");
}

/** The error `fetch` throws when its signal is aborted. */
function abortError() {
  return new DOMException("The operation was aborted.", "AbortError");
}

describe("api client retry policy", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    // Full-jitter backoff would otherwise make these tests sleep for real.
    vi.spyOn(Math, "random").mockReturnValue(0);
    tokenStore.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("non-idempotent methods", () => {
    it("does not replay a POST after a network failure", async () => {
      fetchMock.mockRejectedValue(networkError());

      await expect(api.post("/applications", { flare_id: "x" })).rejects.toBeInstanceOf(ApiError);

      // The whole point: one application attempt means at most one application.
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("does not replay a POST that came back 502", async () => {
      fetchMock.mockResolvedValue(jsonResponse(502, { detail: "Bad gateway" }));

      await expect(api.post("/applications", { flare_id: "x" })).rejects.toMatchObject({
        status: 502,
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("does not replay a POST that timed out", async () => {
      fetchMock.mockRejectedValue(abortError());

      await expect(api.post("/applications")).rejects.toMatchObject({ status: 408 });

      // A timeout is the dangerous case — the write may well have landed.
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("does not replay a PATCH", async () => {
      fetchMock.mockResolvedValue(jsonResponse(503, { detail: "Unavailable" }));

      await expect(api.patch("/applications/1/accept")).rejects.toMatchObject({ status: 503 });

      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("idempotent methods", () => {
    it("retries a GET after a network failure and returns the eventual success", async () => {
      fetchMock
        .mockRejectedValueOnce(networkError())
        .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

      await expect(api.get("/projects")).resolves.toEqual({ ok: true });
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("retries a GET on 500 up to the configured limit", async () => {
      fetchMock.mockResolvedValue(jsonResponse(500, { detail: "boom" }));

      await expect(api.get("/projects")).rejects.toMatchObject({ status: 500 });

      // Default `retries` is 2, so three attempts in total.
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    it("retries a DELETE, which is idempotent by spec", async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse(503, { detail: "Unavailable" }))
        .mockResolvedValueOnce(jsonResponse(204, null));

      await expect(api.delete("/followers/1")).resolves.toBeNull();
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("retries 429, which is the one status that explicitly asks you to", async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse(429, { detail: "Slow down" }))
        .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

      await expect(api.get("/search")).resolves.toEqual({ ok: true });
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("does not retry a 4xx that will fail identically next time", async () => {
      fetchMock.mockResolvedValue(jsonResponse(404, { detail: "Not found" }));

      await expect(api.get("/projects/nope")).rejects.toMatchObject({ status: 404 });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("honours retries: 0", async () => {
      fetchMock.mockResolvedValue(jsonResponse(500, { detail: "boom" }));

      await expect(api.get("/projects", { retries: 0 })).rejects.toMatchObject({ status: 500 });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });

  describe("the idempotent escape hatch", () => {
    it("retries a POST when the caller vouches for it", async () => {
      fetchMock
        .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }))
        .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

      await expect(api.post("/search/reindex", undefined, { idempotent: true })).resolves.toEqual({
        ok: true,
      });

      expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("lets a GET opt out of retrying", async () => {
      fetchMock.mockResolvedValue(jsonResponse(500, { detail: "boom" }));

      await expect(api.get("/expensive", { idempotent: false })).rejects.toMatchObject({
        status: 500,
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("does not forward the flag to the server as a header or body field", async () => {
      fetchMock.mockResolvedValue(jsonResponse(200, {}));

      await api.post("/posts", { content: "hi" }, { idempotent: true });

      const [, init] = fetchMock.mock.calls[0];
      expect(init.body).toBe(JSON.stringify({ content: "hi" }));
      expect(new Headers(init.headers).has("idempotent")).toBe(false);
    });
  });

  describe("cancellation and timeouts", () => {
    it("rejects immediately when the caller's signal is already aborted", async () => {
      const controller = new AbortController();
      controller.abort();

      await expect(api.get("/projects", { signal: controller.signal })).rejects.toMatchObject({
        status: 408,
      });

      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("stops retrying once the caller aborts mid-flight", async () => {
      const controller = new AbortController();
      fetchMock.mockImplementation(() => {
        controller.abort();
        return Promise.reject(abortError());
      });

      await expect(api.get("/projects", { signal: controller.signal })).rejects.toMatchObject({
        status: 408,
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it("does not leave an abort listener behind for every attempt", async () => {
      const controller = new AbortController();
      const addSpy = vi.spyOn(controller.signal, "addEventListener");
      const removeSpy = vi.spyOn(controller.signal, "removeEventListener");

      fetchMock.mockResolvedValue(jsonResponse(500, { detail: "boom" }));

      await expect(api.get("/projects", { signal: controller.signal })).rejects.toBeInstanceOf(
        ApiError,
      );

      expect(addSpy).toHaveBeenCalledTimes(3);
      expect(removeSpy).toHaveBeenCalledTimes(3);
    });

    it("passes a signal to fetch on every attempt, including the first", async () => {
      fetchMock.mockResolvedValue(jsonResponse(200, {}));

      await api.get("/projects");

      const [, init] = fetchMock.mock.calls[0];
      expect(init.signal).toBeInstanceOf(AbortSignal);
    });
  });

  describe("maintenance mode", () => {
    it("does not throw when there is no window (SSR)", async () => {
      const originalWindow = globalThis.window;
      // Simulate a server-side render, where `window.location` is not there.
      // @ts-expect-error deliberately removing a global for this assertion
      delete globalThis.window;

      fetchMock.mockResolvedValue(jsonResponse(503, { detail: "Maintenance Mode" }));

      try {
        await expect(api.get("/projects", { retries: 0 })).rejects.toMatchObject({ status: 503 });
      } finally {
        globalThis.window = originalWindow;
      }
    });
  });

  describe("error surfacing", () => {
    it("prefers a nested error.message over detail", async () => {
      fetchMock.mockResolvedValue(
        jsonResponse(400, { error: { message: "Flare is closed" }, detail: "Bad request" }),
      );

      await expect(api.post("/applications")).rejects.toMatchObject({
        message: "Flare is closed",
        status: 400,
      });
    });

    it("falls back to detail", async () => {
      fetchMock.mockResolvedValue(jsonResponse(400, { detail: "Bad request" }));

      await expect(api.post("/applications")).rejects.toMatchObject({
        message: "Bad request",
      });
    });

    it("reports a network failure as status 0", async () => {
      fetchMock.mockRejectedValue(networkError());

      await expect(request("/projects", { method: "POST" })).rejects.toMatchObject({ status: 0 });
    });
  });
});

describe("parseRetryAfter", () => {
  const NOW = Date.parse("2026-08-12T10:00:00Z");

  it("returns null for an absent header", () => {
    expect(parseRetryAfter(null, NOW)).toBeNull();
  });

  it("returns null for an empty header", () => {
    expect(parseRetryAfter("   ", NOW)).toBeNull();
  });

  it("reads delta-seconds", () => {
    expect(parseRetryAfter("3", NOW)).toBe(3000);
  });

  it("reads the HTTP-date form", () => {
    expect(parseRetryAfter("Wed, 12 Aug 2026 10:00:05 GMT", NOW)).toBe(5000);
  });

  it("treats a date in the past as retry now", () => {
    expect(parseRetryAfter("Wed, 12 Aug 2026 09:59:00 GMT", NOW)).toBe(0);
  });

  it("caps an absurd wait rather than hanging the request", () => {
    expect(parseRetryAfter("86400", NOW)).toBe(20_000);
  });

  it("returns null for something it cannot parse", () => {
    expect(parseRetryAfter("soon please", NOW)).toBeNull();
  });

  it("rejects a negative delta rather than reading it as a date", () => {
    expect(parseRetryAfter("-5", NOW)).toBeNull();
  });
});

describe("backoffDelay", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("grows exponentially at the top of the jitter window", () => {
    vi.spyOn(Math, "random").mockReturnValue(1);

    expect(backoffDelay(0)).toBe(200);
    expect(backoffDelay(1)).toBe(400);
    expect(backoffDelay(2)).toBe(800);
  });

  it("can return zero, so retries are spread rather than synchronised", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);

    expect(backoffDelay(3)).toBe(0);
  });

  it("caps the window so a long retry chain does not stall for minutes", () => {
    vi.spyOn(Math, "random").mockReturnValue(1);

    expect(backoffDelay(20)).toBe(8000);
  });
});

/**
 * The refresh path only engages when a base URL is configured, so these load a
 * fresh copy of the module with `VITE_API_BASE_URL` stubbed. Without that,
 * `refreshAccessToken` short-circuits and the replay never happens — a test
 * written against the default module passes without exercising anything.
 */
describe("the post-refresh replay", () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  let client: typeof import("../client");

  beforeEach(async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.test");
    vi.resetModules();

    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(Math, "random").mockReturnValue(0);

    client = await import("../client");
    const tokens = await import("../tokens");
    tokens.tokenStore.set("stale-access", "refresh-token");
  });

  afterEach(async () => {
    const tokens = await import("../tokens");
    tokens.tokenStore.clear();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("replays the request once with the refreshed token", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: "fresh" }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    await expect(client.api.get("/projects", { retries: 0 })).resolves.toEqual({ ok: true });

    const [, replayInit] = fetchMock.mock.calls[2];
    expect(new Headers(replayInit.headers).get("Authorization")).toBe("Bearer fresh");
  });

  it("gives the replay a signal, so it can time out and be cancelled", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: "fresh" }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    await client.api.get("/projects", { retries: 0 });

    // Previously this was a bare fetch with no signal at all.
    const [, replayInit] = fetchMock.mock.calls[2];
    expect(replayInit.signal).toBeInstanceOf(AbortSignal);
  });

  it("surfaces a network failure during the replay as an ApiError", async () => {
    // The replay sits outside the retry loop, so nothing there would convert a
    // raw fetch rejection. Callers only ever catch ApiError.
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: "fresh" }))
      .mockRejectedValueOnce(networkError());

    await expect(client.api.get("/projects", { retries: 0 })).rejects.toBeInstanceOf(
      client.ApiError,
    );
  });

  it("surfaces an abort during the replay as a 408", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: "fresh" }))
      .mockRejectedValueOnce(abortError());

    await expect(client.api.get("/projects", { retries: 0 })).rejects.toMatchObject({
      status: 408,
    });
  });

  it("does not replay when the refresh itself fails", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Expired" }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Refresh rejected" }));

    await expect(client.api.get("/projects", { retries: 0 })).rejects.toMatchObject({
      status: 401,
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
