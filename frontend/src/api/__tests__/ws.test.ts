/**
 * WebSocket client lifecycle.
 *
 * The client is a module-level singleton, but sign-in and sign-out change
 * identity underneath it. Most of what is asserted here is about what the
 * client does *across* that boundary: which rooms it re-joins, whether a
 * deliberate close stays closed, and whether the socket keeps the identity it
 * was opened with after the token changes.
 *
 * `VITE_API_BASE_URL` has to be set before `client.ts` is imported, since it
 * reads the env var at module scope. Hence the dynamic imports.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ── A WebSocket good enough to assert against ────────────────────────────────

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  /** Every socket constructed during a test, in order. */
  static instances: FakeWebSocket[] = [];

  /** Constructor throws once, for the "cannot open" path. */
  static throwOnNextConstruct = false;

  readyState = FakeWebSocket.CONNECTING;
  sent: string[] = [];
  closeCalls = 0;

  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    if (FakeWebSocket.throwOnNextConstruct) {
      FakeWebSocket.throwOnNextConstruct = false;
      throw new Error("cannot open");
    }
    FakeWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.closeCalls += 1;
    const wasOpen = this.readyState !== FakeWebSocket.CLOSED;
    this.readyState = FakeWebSocket.CLOSED;
    if (wasOpen) this.onclose?.();
  }

  // -- test helpers --

  /** Complete the handshake. */
  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  /** Drop the connection the way a server restart would. */
  dropped() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  deliver(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  /** The messages sent on this socket, parsed. */
  get messages(): Array<Record<string, unknown>> {
    return this.sent.map((raw) => JSON.parse(raw));
  }

  static get latest(): FakeWebSocket {
    return FakeWebSocket.instances[FakeWebSocket.instances.length - 1];
  }

  static reset() {
    FakeWebSocket.instances = [];
    FakeWebSocket.throwOnNextConstruct = false;
  }
}

// ── Harness ──────────────────────────────────────────────────────────────────

let ws: typeof import("../ws").ws;
let reconnectDelay: typeof import("../ws").reconnectDelay;
let tokenStore: typeof import("../tokens").tokenStore;

async function loadModules() {
  vi.resetModules();
  vi.stubEnv("VITE_API_BASE_URL", "http://api.test");

  const tokensModule = await import("../tokens");
  tokenStore = tokensModule.tokenStore;

  const wsModule = await import("../ws");
  ws = wsModule.ws;
  reconnectDelay = wsModule.reconnectDelay;
}

/** Sign in, open the socket, and complete the handshake. */
function signIn(token = "access-token-a") {
  tokenStore.set(token, "refresh-token");
  FakeWebSocket.latest.open();
}

beforeEach(async () => {
  vi.useFakeTimers();
  FakeWebSocket.reset();
  vi.stubGlobal("WebSocket", FakeWebSocket);
  window.localStorage.clear();
  window.sessionStorage.clear();
  await loadModules();
});

afterEach(() => {
  ws?.disconnect();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

// ── Rooms across a session boundary ──────────────────────────────────────────

describe("project rooms", () => {
  it("does not re-join the previous session's rooms after a sign-out", () => {
    // The bug. User A opens a project...
    signIn("token-user-a");
    ws.joinProject("project-owned-by-a");
    expect(ws.getJoinedProjects()).toEqual(["project-owned-by-a"]);

    // ...signs out...
    tokenStore.clear();
    expect(ws.getJoinedProjects()).toEqual([]);

    // ...and user B signs in in the same tab.
    tokenStore.set("token-user-b", "refresh-b");
    FakeWebSocket.latest.open();

    const joins = FakeWebSocket.latest.messages.filter((m) => m.type === "join");
    expect(joins).toEqual([]);
  });

  it("re-joins its own rooms after a dropped connection", () => {
    signIn();
    ws.joinProject("project-1");
    ws.joinProject("project-2");

    const first = FakeWebSocket.latest;
    first.dropped();

    vi.advanceTimersByTime(MAX_DELAY);
    FakeWebSocket.latest.open();

    const joined = FakeWebSocket.latest.messages
      .filter((m) => m.type === "join")
      .map((m) => m.project_id);
    expect(joined.sort()).toEqual(["project-1", "project-2"]);
  });

  it("does not re-join a room that was left", () => {
    signIn();
    ws.joinProject("project-1");
    ws.joinProject("project-2");
    ws.leaveProject("project-1");

    FakeWebSocket.latest.dropped();
    vi.advanceTimersByTime(MAX_DELAY);
    FakeWebSocket.latest.open();

    const joined = FakeWebSocket.latest.messages
      .filter((m) => m.type === "join")
      .map((m) => m.project_id);
    expect(joined).toEqual(["project-2"]);
  });

  it("clears rooms on an explicit disconnect", () => {
    signIn();
    ws.joinProject("project-1");

    ws.disconnect();

    expect(ws.getJoinedProjects()).toEqual([]);
  });
});

// ── Manual close ─────────────────────────────────────────────────────────────

describe("manual close", () => {
  it("is not revived by subscribing", () => {
    // `on()` used to reconnect whenever `socket` was null, and `connect()`
    // reset `manualClose` -- so any component mounting after a sign-out
    // reopened the connection.
    signIn();
    const opened = FakeWebSocket.instances.length;

    ws.disconnect();
    const off = ws.on(() => {});

    expect(FakeWebSocket.instances.length).toBe(opened);
    off();
  });

  it("does not schedule a reconnect", () => {
    signIn();
    const opened = FakeWebSocket.instances.length;

    ws.disconnect();
    vi.advanceTimersByTime(MAX_DELAY * 5);

    expect(FakeWebSocket.instances.length).toBe(opened);
    expect(ws.getStatus()).toBe("closed");
  });

  it("can be reopened deliberately", () => {
    signIn();
    ws.disconnect();

    ws.retry();

    expect(FakeWebSocket.latest).toBeDefined();
    expect(ws.getStatus()).toBe("connecting");
  });
});

// ── Token changes ────────────────────────────────────────────────────────────

describe("token changes", () => {
  it("opens the socket with the current token", () => {
    signIn("token-abc");

    expect(FakeWebSocket.latest.url).toContain("token=token-abc");
  });

  it("reconnects when the token is replaced under an open socket", () => {
    // A WebSocket authenticates once, at the handshake. There is no way to
    // re-authenticate an open one, so a token change has to mean a new socket
    // -- otherwise it keeps the identity it was opened with.
    signIn("token-user-a");
    const first = FakeWebSocket.latest;

    tokenStore.set("token-user-b", "refresh-b");

    expect(FakeWebSocket.latest).not.toBe(first);
    expect(FakeWebSocket.latest.url).toContain("token=token-user-b");
  });

  it("does not reconnect when the same token is set again", () => {
    signIn("token-abc");
    const opened = FakeWebSocket.instances.length;

    tokenStore.set("token-abc", "refresh-token");

    expect(FakeWebSocket.instances.length).toBe(opened);
  });

  it("does not open a socket without a token", () => {
    ws.connect();

    expect(FakeWebSocket.instances).toHaveLength(0);
  });
});

// ── Reconnection ─────────────────────────────────────────────────────────────

const MAX_DELAY = 30_000;

describe("reconnection", () => {
  it("applies jitter to the delay", () => {
    // Deterministic "random" so the window, not the draw, is under test.
    const random = vi.spyOn(Math, "random");

    random.mockReturnValue(0);
    expect(reconnectDelay(0)).toBe(0);

    random.mockReturnValue(1);
    expect(reconnectDelay(0)).toBe(1000);

    random.mockReturnValue(0.5);
    expect(reconnectDelay(1)).toBe(1000);

    random.mockRestore();
  });

  it("caps the delay", () => {
    const random = vi.spyOn(Math, "random").mockReturnValue(1);

    expect(reconnectDelay(20)).toBe(MAX_DELAY);

    random.mockRestore();
  });

  it("spreads two clients that dropped at the same moment", () => {
    // The point of jitter: without it, every tab reconnects on the same tick.
    const draws = [0.1, 0.9];
    let index = 0;
    const random = vi.spyOn(Math, "random").mockImplementation(() => draws[index++ % 2]);

    expect(reconnectDelay(3)).not.toBe(reconnectDelay(3));

    random.mockRestore();
  });

  it("reconnects after a dropped connection", () => {
    signIn();
    const first = FakeWebSocket.latest;

    first.dropped();
    expect(ws.getStatus()).toBe("reconnecting");

    vi.advanceTimersByTime(MAX_DELAY);

    expect(FakeWebSocket.latest).not.toBe(first);
  });

  it("gives up after the attempt limit", () => {
    signIn();

    // Each cycle: the pending socket drops, the timer fires, a new one opens.
    for (let i = 0; i < 12; i += 1) {
      FakeWebSocket.latest?.dropped();
      vi.advanceTimersByTime(MAX_DELAY);
    }

    expect(ws.getStatus()).toBe("gave-up");

    const settled = FakeWebSocket.instances.length;
    vi.advanceTimersByTime(MAX_DELAY * 5);
    expect(FakeWebSocket.instances.length).toBe(settled);
  });

  it("resets the attempt budget on a successful open", () => {
    signIn();

    FakeWebSocket.latest.dropped();
    vi.advanceTimersByTime(MAX_DELAY);
    FakeWebSocket.latest.open();

    // Having reconnected once, the budget is full again -- so a long outage
    // later is not shortened by failures from an outage hours ago.
    for (let i = 0; i < 9; i += 1) {
      FakeWebSocket.latest?.dropped();
      vi.advanceTimersByTime(MAX_DELAY);
    }

    expect(ws.getStatus()).not.toBe("closed");
    expect(FakeWebSocket.instances.length).toBeGreaterThan(2);
  });

  it("schedules a reconnect when the socket cannot be constructed", () => {
    // Armed before the token is set, since setting it is what triggers the
    // connect. Arming afterwards would hit the already-connecting guard and
    // never reach the constructor.
    FakeWebSocket.throwOnNextConstruct = true;

    tokenStore.set("token", "refresh");

    expect(FakeWebSocket.instances).toHaveLength(0);
    expect(ws.getStatus()).toBe("reconnecting");

    // And it recovers on the next attempt.
    vi.advanceTimersByTime(MAX_DELAY);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("does not burn attempts while offline", () => {
    signIn();
    const opened = FakeWebSocket.instances.length;

    const onLine = vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);

    FakeWebSocket.latest.dropped();
    vi.advanceTimersByTime(MAX_DELAY * 3);

    expect(FakeWebSocket.instances.length).toBe(opened);

    onLine.mockRestore();
  });

  it("resumes when the browser comes back online", () => {
    signIn();
    const onLine = vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);

    FakeWebSocket.latest.dropped();
    vi.advanceTimersByTime(MAX_DELAY);
    const stalled = FakeWebSocket.instances.length;

    onLine.mockReturnValue(true);
    window.dispatchEvent(new Event("online"));

    expect(FakeWebSocket.instances.length).toBeGreaterThan(stalled);

    onLine.mockRestore();
  });
});

// ── Events ───────────────────────────────────────────────────────────────────

describe("events", () => {
  it("delivers parsed messages to handlers", () => {
    signIn();
    const seen: unknown[] = [];
    const off = ws.on((event) => seen.push(event));

    FakeWebSocket.latest.deliver({ type: "presence", userId: "u1", online: true });

    expect(seen).toEqual([{ type: "presence", userId: "u1", online: true }]);
    off();
  });

  it("ignores malformed messages", () => {
    signIn();
    const seen: unknown[] = [];
    const off = ws.on((event) => seen.push(event));

    expect(() => FakeWebSocket.latest.onmessage?.({ data: "not json" })).not.toThrow();
    expect(seen).toEqual([]);
    off();
  });

  it("stops delivering after unsubscribing", () => {
    signIn();
    const seen: unknown[] = [];
    const off = ws.on((event) => seen.push(event));

    off();
    FakeWebSocket.latest.deliver({ type: "presence", userId: "u1", online: true });

    expect(seen).toEqual([]);
  });

  it("does not send on a socket that is not open", () => {
    tokenStore.set("token", "refresh");
    // Constructed but the handshake has not completed.
    expect(() => ws.send({ type: "join", project_id: "p" })).not.toThrow();
    expect(FakeWebSocket.latest.sent).toEqual([]);
  });
});

// ── Status ───────────────────────────────────────────────────────────────────

describe("status", () => {
  it("reports the current status to a new subscriber", () => {
    const seen: string[] = [];
    const off = ws.onStatus((s) => seen.push(s));

    expect(seen).toEqual(["closed"]);
    off();
  });

  it("moves through connecting and open", () => {
    const seen: string[] = [];
    const off = ws.onStatus((s) => seen.push(s));

    signIn();

    expect(seen).toEqual(["closed", "connecting", "open"]);
    off();
  });

  it("stops notifying after unsubscribing", () => {
    const seen: string[] = [];
    const off = ws.onStatus((s) => seen.push(s));
    off();

    signIn();

    expect(seen).toEqual(["closed"]);
  });
});
