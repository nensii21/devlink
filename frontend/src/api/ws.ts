// WebSocket manager for chat, notifications, typing, presence, read receipts.
// Auto-reconnect with backoff, JWT auth via query param, typed event bus.

import { tokenStore } from "./tokens";
import { API_BASE_URL, isBackendConfigured } from "./client";

export type WsEvent =
  | { type: "message"; conversationId: string; from: string; text: string; at: string; id: string }
  | { type: "typing"; conversationId: string; from: string; typing: boolean }
  | { type: "read"; conversationId: string; by: string; at: string }
  | { type: "presence"; userId: string; online: boolean }
  | { type: "notification"; id: string; kind: string; text: string; at: string }
  | { type: string; [k: string]: unknown };

type Handler = (ev: WsEvent) => void;

function wsUrl(): string {
  if (!isBackendConfigured()) return "";
  const base = API_BASE_URL.replace(/^http/, "ws");
  const token = tokenStore.getAccess();
  return `${base}/ws${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

class WsClient {
  private socket: WebSocket | null = null;
  private handlers = new Set<Handler>();
  private reconnectAttempts = 0;
  private manualClose = false;
  private connectTimer: ReturnType<typeof setTimeout> | null = null;

  connect() {
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
    };
    this.socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as WsEvent;
        this.handlers.forEach((h) => h(data));
      } catch {
        /* ignore malformed */
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

  private scheduleReconnect() {
    if (this.connectTimer) return;
    const delay = Math.min(30_000, 1000 * 2 ** this.reconnectAttempts);
    this.reconnectAttempts += 1;
    this.connectTimer = setTimeout(() => {
      this.connectTimer = null;
      this.connect();
    }, delay);
  }

  send(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  disconnect() {
    this.manualClose = true;
    this.socket?.close();
    this.socket = null;
  }

  on(handler: Handler): () => void {
    this.handlers.add(handler);
    if (!this.socket) this.connect();
    return () => {
      this.handlers.delete(handler);
    };
  }
}

export const ws = new WsClient();

// Reconnect when auth changes.
if (typeof window !== "undefined") {
  tokenStore.subscribe((t) => {
    if (t) ws.connect();
    else ws.disconnect();
  });
}
