// WebSocket manager for real-time team collaboration.
//
// Features:
//   - JWT auth via query param (browsers can't send headers on WS)
//   - Auto-reconnect with exponential backoff (capped at 30s)
//   - Project-scoped rooms (join/leave to receive project events)
//   - Typed event bus for team collaboration events
//   - Graceful handling of disconnections
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

// ── WebSocket URL ────────────────────────────────────────────────────────────

function wsUrl(): string {
  if (!isBackendConfigured()) return "";
  const base = API_BASE_URL.replace(/^http/, "ws");
  const token = tokenStore.getAccess();
  return `${base}/ws/collab${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

// ── WsClient ─────────────────────────────────────────────────────────────────

class WsClient {
  private socket: WebSocket | null = null;
  private handlers = new Set<Handler>();
  private reconnectAttempts = 0;
  private manualClose = false;
  private connectTimer: ReturnType<typeof setTimeout> | null = null;
  private joinedProjects = new Set<string>();

  /** Open the WebSocket connection (idempotent). */
  connect(): void {
    if (!isBackendConfigured() || typeof window === "undefined") return;
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) return;
    this.manualClose = false;
    try {
      const url = wsUrl();
      if (!url) return;
      this.socket = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      // Re-join any project rooms that were active before the reconnect.
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
      if (!this.manualClose) this.scheduleReconnect();
    };

    this.socket.onerror = () => {
      this.socket?.close();
    };
  }

  /** Schedule a reconnection with exponential backoff (capped at 30s). */
  private scheduleReconnect(): void {
    if (this.connectTimer) return;
    const delay = Math.min(30_000, 1000 * 2 ** this.reconnectAttempts);
    this.reconnectAttempts += 1;
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

  /** Close the connection and stop auto-reconnect. */
  disconnect(): void {
    this.manualClose = true;
    this.socket?.close();
    this.socket = null;
    if (this.connectTimer) {
      clearTimeout(this.connectTimer);
      this.connectTimer = null;
    }
  }

  /** Register an event handler. Returns an unsubscribe function. */
  on(handler: Handler): () => void {
    this.handlers.add(handler);
    if (!this.socket) this.connect();
    return () => {
      this.handlers.delete(handler);
    };
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
    if (t) ws.connect();
    else ws.disconnect();
  });
}
