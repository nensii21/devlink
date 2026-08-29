// WebSocket manager for real-time team collaboration.
//
// Features:
//   - JWT auth via query param (browsers can't send headers on WS)
//   - Auto-reconnect with jittered exponential backoff (capped at 30s)
//   - Project-scoped rooms (join/leave to receive project events)
//   - Typed event bus for team collaboration events
//   - Graceful handling of disconnections
//
// This is a module-level singleton, but sign-in and sign-out change identity
// underneath it. Everything below that looks like defensive bookkeeping is
// there because the connection outlives the session that opened it:
//
//   - `disconnect()` clears the joined rooms, so a new session does not
//     re-join the previous user's projects on its first `onopen`.
//   - A manual close stays closed. Subscribing does not silently reopen it.
//   - The token the socket was opened with is remembered, so a refresh (or a
//     different user signing in) reconnects rather than leaving the socket
//     authenticated as whoever opened it.
//
// Usage:
//   import { ws } from "@/api/ws";
//
//   // Join a project room
//   ws.joinProject("project-uuid");
//
//   // Listen for events
//   const off = ws.on((event) => {
//     if (event.type === "team.member_joined") { ... }
//   });
//
//   // Leave when done
//   ws.leaveProject("project-uuid");
//   off();

import { tokenStore } from "./tokens";
import { API_BASE_URL, isBackendConfigured } from "./client";

// ── Event types ──────────────────────────────────────────────────────────────

export type CollabEvent =
  | { type: "connected"; user_id: string }
  | { type: "team.member_joined"; project_id: string; user_id: string }
  | { type: "team.member_left"; project_id: string; user_id: string }
  | {
      type: "project.updated";
      project_id: string;
      user_id: string;
      changes: Record<string, unknown>;
    }
  | { type: "message.new"; project_id: string; user_id: string; content: string }
  | {
      type: "task.status_changed";
      project_id: string;
      user_id: string;
      task_id: string;
      status: string;
    }
  | { type: "message"; conversationId: string; from: string; text: string; at: string; id: string }
  | { type: "typing"; conversationId: string; from: string; typing: boolean }
  | { type: "read"; conversationId: string; by: string; at: string }
  | { type: "presence"; userId: string; online: boolean }
  | {
      type: "presence.collaboration_status_changed";
      userId: string;
      status: string;
    }
  | { type: "presence.query_response"; presences: Record<string, string> }
  | { type: "notification"; id: string; kind: string; text: string; at: string }
  | { type: "status"; sender_id: string; content: string }
  | { type: "error"; message: string }
  | { type: string; [k: string]: unknown };

type Handler = (ev: CollabEvent) => void;

/** What the client is currently doing, for anything that wants to show it. */
export type WsStatus = "closed" | "connecting" | "open" | "reconnecting" | "gave-up";

type StatusListener = (status: WsStatus) => void;

// ── Tuning ───────────────────────────────────────────────────────────────────

/** Ceiling on the backoff window. */
const MAX_RECONNECT_DELAY_MS = 30_000;

/** First backoff window, doubled per attempt. */
const BASE_RECONNECT_DELAY_MS = 1_000;

/**
 * How many consecutive failures before the client stops trying.
 *
 * Unbounded reconnection means a backgrounded tab retries every 30s forever
 * against a server that may have been gone for hours. Ten attempts spans
 * roughly four minutes of real outage, after which something has to
 * explicitly ask for a reconnect — which `online` and a token change both do.
 */
const MAX_RECONNECT_ATTEMPTS = 10;

// ── WebSocket URL ────────────────────────────────────────────────────────────

function wsUrl(token: string): string {
  if (!isBackendConfigured()) return "";
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}/ws/collab?token=${encodeURIComponent(token)}`;
}

/**
 * Backoff with full jitter.
 *
 * Without jitter every tab that was connected when the server restarted
 * reconnects on exactly the same tick, and keeps doing so in lockstep — the
 * precise load pattern a recovering server does not need. `client.ts` already
 * applies full jitter to HTTP retries for this reason; this is the same
 * argument for the socket.
 *
 * Exported for the tests, which stub `Math.random` to make the delay
 * deterministic.
 */
export function reconnectDelay(attempt: number): number {
  const ceiling = Math.min(BASE_RECONNECT_DELAY_MS * 2 ** attempt, MAX_RECONNECT_DELAY_MS);
  return Math.round(Math.random() * ceiling);
}

// ── WsClient ─────────────────────────────────────────────────────────────────

class WsClient {
  private socket: WebSocket | null = null;
  private handlers = new Set<Handler>();
  private statusListeners = new Set<StatusListener>();
  private reconnectAttempts = 0;
  private manualClose = false;
  private connectTimer: ReturnType<typeof setTimeout> | null = null;
  private joinedProjects = new Set<string>();
  private status: WsStatus = "closed";

  /**
   * The token the current socket was opened with.
   *
   * A WebSocket authenticates once, at the handshake, from the token in its
   * URL. There is no way to re-authenticate an open socket, so when the token
   * changes the only correct response is to open a new one. Without this the
   * socket kept whatever identity it was opened with — including across a
   * sign-out and a sign-in as somebody else.
   */
  private socketToken: string | null = null;

  /** Open the WebSocket connection (idempotent). */
  connect(): void {
    if (!isBackendConfigured() || typeof window === "undefined") return;

    const token = tokenStore.getAccess();

    // No credential, no socket. Opening one anyway just produces a handshake
    // the server rejects, followed by the reconnect loop retrying it.
    if (!token) return;

    // Already connected or connecting with this same token.
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) {
      if (this.socketToken === token) return;
      // Token changed under an open socket. Tear it down without letting the
      // close handler schedule a reconnect, then fall through and reopen.
      this.closeSocket();
    }

    this.manualClose = false;
    this.clearTimer();
    this.setStatus("connecting");

    const url = wsUrl(token);
    if (!url) return;

    try {
      this.socket = new WebSocket(url);
      this.socketToken = token;
    } catch {
      this.socket = null;
      this.socketToken = null;
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus("open");
      // Re-join the rooms that were active before the reconnect. This set is
      // cleared on disconnect, so it only ever contains rooms belonging to
      // the session that is currently open.
      for (const projectId of this.joinedProjects) {
        this.send({ type: "join", project_id: projectId });
      }
    };

    this.socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as CollabEvent;
        this.handlers.forEach((h) => h(data));
      } catch {
        /* ignore malformed messages */
      }
    };

    this.socket.onclose = () => {
      this.socket = null;
      this.socketToken = null;
      if (this.manualClose) {
        this.setStatus("closed");
        return;
      }
      this.scheduleReconnect();
    };

    this.socket.onerror = () => {
      this.socket?.close();
    };
  }

  /** Detach the handlers and close, without triggering a reconnect. */
  private closeSocket(): void {
    const socket = this.socket;
    this.socket = null;
    this.socketToken = null;

    if (!socket) return;

    // Cleared first: `close()` fires `onclose`, and this path is a deliberate
    // replacement rather than a dropped connection.
    socket.onopen = null;
    socket.onmessage = null;
    socket.onclose = null;
    socket.onerror = null;

    try {
      socket.close();
    } catch {
      /* already closing */
    }
  }

  private clearTimer(): void {
    if (this.connectTimer) {
      clearTimeout(this.connectTimer);
      this.connectTimer = null;
    }
  }

  private setStatus(status: WsStatus): void {
    if (this.status === status) return;
    this.status = status;
    this.statusListeners.forEach((l) => l(status));
  }

  /** Schedule a reconnection with jittered exponential backoff. */
  private scheduleReconnect(): void {
    if (this.connectTimer || this.manualClose) return;

    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this.setStatus("gave-up");
      return;
    }

    // Offline is not a server problem, and burning attempts against a
    // disconnected network just exhausts the budget before the network comes
    // back. The `online` listener below resumes.
    if (typeof navigator !== "undefined" && navigator.onLine === false) {
      this.setStatus("reconnecting");
      return;
    }

    const delay = reconnectDelay(this.reconnectAttempts);
    this.reconnectAttempts += 1;
    this.setStatus("reconnecting");

    this.connectTimer = setTimeout(() => {
      this.connectTimer = null;
      this.connect();
    }, delay);
  }

  /** Send a JSON payload to the server (no-op if socket isn't open). */
  send(payload: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  /**
   * Close the connection and stop auto-reconnect.
   *
   * Clears the joined rooms. It did not, so the room set survived a sign-out
   * and the next session's first `onopen` sent a `join` for every project the
   * previous user had open.
   */
  disconnect(): void {
    this.manualClose = true;
    this.clearTimer();
    this.reconnectAttempts = 0;
    this.joinedProjects.clear();
    this.closeSocket();
    this.setStatus("closed");
  }

  /**
   * Register an event handler. Returns an unsubscribe function.
   *
   * Subscribing connects only when the client has not been deliberately
   * closed. Previously this reconnected whenever `socket` was null, and
   * `connect()` reset `manualClose` — so any component mounting after a
   * sign-out reopened the connection.
   */
  on(handler: Handler): () => void {
    this.handlers.add(handler);
    if (!this.socket && !this.manualClose) this.connect();
    return () => {
      this.handlers.delete(handler);
    };
  }

  /** Observe connection status. Returns an unsubscribe function. */
  onStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  /** Current connection status. */
  getStatus(): WsStatus {
    return this.status;
  }

  /** The rooms this client will (re-)join. Exposed for tests and debugging. */
  getJoinedProjects(): string[] {
    return [...this.joinedProjects];
  }

  /**
   * Try again after the client gave up, or after coming back online.
   *
   * Resets the attempt counter, which is what separates this from `connect()`.
   */
  retry(): void {
    this.reconnectAttempts = 0;
    this.manualClose = false;
    this.connect();
  }

  // ── Project room management ──────────────────────────────────────────

  /** Join a project room to receive project-scoped events. */
  joinProject(projectId: string): void {
    this.joinedProjects.add(projectId);
    this.send({ type: "join", project_id: projectId });
  }

  /** Leave a project room. */
  leaveProject(projectId: string): void {
    this.joinedProjects.delete(projectId);
    this.send({ type: "leave", project_id: projectId });
  }

  /** Send a chat message to a project room. */
  sendProjectMessage(projectId: string, content: string): void {
    this.send({ type: "message", project_id: projectId, content });
  }

  /** Notify a project room that a task's status changed. */
  notifyTaskUpdate(projectId: string, taskId: string, taskStatus: string): void {
    this.send({ type: "task_update", project_id: projectId, task_id: taskId, status: taskStatus });
  }

  /** Notify a project room that project metadata changed. */
  notifyProjectUpdate(projectId: string, changes: Record<string, unknown>): void {
    this.send({ type: "project_update", project_id: projectId, changes });
  }

  // ── Collaboration presence ────────────────────────────────────────────────

  /** Broadcast a collaboration status change to all connected users. */
  updateCollaborationStatus(status: string): void {
    this.send({ type: "collaboration_status_update", status });
  }

  /** Query presence statuses. Pass user_ids to query specific users. */
  queryPresence(userIds?: string[]): void {
    this.send({ type: "presence_query", user_ids: userIds });
  }
}

export const ws = new WsClient();

// ── Auto-connect / disconnect on auth change ─────────────────────────────────

if (typeof window !== "undefined") {
  tokenStore.subscribe((t) => {
    // `connect()` compares the new token against the one the socket was
    // opened with, so a refresh reconnects rather than leaving the socket
    // authenticated as whoever opened it.
    if (t) ws.connect();
    else ws.disconnect();
  });

  // Coming back online resets the attempt budget. Without this a tab that
  // exhausted its attempts during an outage stays dead until it is reloaded.
  window.addEventListener("online", () => {
    if (tokenStore.getAccess()) ws.retry();
  });
}
