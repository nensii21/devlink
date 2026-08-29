import { useState, useEffect, useRef, useCallback } from "react";
import { tokenStore } from "@/api/tokens";

export interface ChatWebSocketEvent {
  type: string;
  conversation_id: string;
  user_id: string;
  content?: string;
}

const BASE_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;
const MAX_RECONNECT_ATTEMPTS = 10;

export function getReconnectDelay(attempt: number): number {
  const ceiling = Math.min(BASE_RECONNECT_DELAY_MS * 2 ** attempt, MAX_RECONNECT_DELAY_MS);
  return Math.round(Math.random() * ceiling);
}

export function useChatWebSocket(
  conversationId: string,
  currentUserId: string,
  onNewMessage: (msg: unknown) => void,
) {
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isUnmountedRef = useRef(false);
  const onNewMessageRef = useRef(onNewMessage);
  const currentUserIdRef = useRef(currentUserId);
  const typingTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Keep latest callbacks without triggering WebSocket re-instantiation
  useEffect(() => {
    onNewMessageRef.current = onNewMessage;
  }, [onNewMessage]);

  useEffect(() => {
    currentUserIdRef.current = currentUserId;
  }, [currentUserId]);

  useEffect(() => {
    isUnmountedRef.current = false;
    const typingTimers = typingTimersRef.current;

    // Clear existing timers for previous conversation
    typingTimers.forEach((timer) => clearTimeout(timer));
    typingTimers.clear();

    // Reset reconnect attempts on conversation change
    reconnectAttemptsRef.current = 0;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (!conversationId) {
      return;
    }

    function cleanupSocket(socket: WebSocket | null) {
      if (!socket) return;
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      socket.onerror = null;

      if (socket.readyState === WebSocket.OPEN) {
        try {
          socket.send(JSON.stringify({ type: "chat.leave", conversation_id: conversationId }));
        } catch {
          // Ignore send errors during cleanup
        }
      }

      try {
        socket.close();
      } catch {
        // Ignore close errors
      }
    }

    function connect() {
      if (isUnmountedRef.current || !conversationId) return;

      const protocol =
        typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = typeof window !== "undefined" ? window.location.host : "localhost";
      const token =
        tokenStore.getAccess() ||
        (typeof localStorage !== "undefined"
          ? localStorage.getItem("devlink_access_token")
          : null) ||
        "demo-token";
      const wsUrl = `${protocol}//${host}/api/v1/ws/collab?token=${encodeURIComponent(token)}`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isUnmountedRef.current || wsRef.current !== ws) {
            cleanupSocket(ws);
            return;
          }
          reconnectAttemptsRef.current = 0;
          setIsConnected(true);
          // Join the conversation room
          try {
            ws.send(JSON.stringify({ type: "chat.join", conversation_id: conversationId }));
          } catch {
            // Ignore send errors
          }
        };

        ws.onmessage = (evt) => {
          if (isUnmountedRef.current || wsRef.current !== ws) return;

          try {
            const msg = JSON.parse(evt.data);

            if (msg.type === "chat.message.new" && msg.conversation_id === conversationId) {
              onNewMessageRef.current?.(msg);
            } else if (msg.type === "chat.typing" && msg.conversation_id === conversationId) {
              const userId = msg.user_id;
              if (userId && userId !== currentUserIdRef.current) {
                setTypingUsers((prev) => {
                  const newSet = new Set(prev);
                  newSet.add(userId);
                  return newSet;
                });

                // Clear any existing typing timer for this user
                const prevTimer = typingTimers.get(userId);
                if (prevTimer) clearTimeout(prevTimer);

                // Clear typing indicator after 3 seconds
                const timer = setTimeout(() => {
                  typingTimers.delete(userId);
                  if (isUnmountedRef.current) return;
                  setTypingUsers((prev) => {
                    const newSet = new Set(prev);
                    newSet.delete(userId);
                    return newSet;
                  });
                }, 3000);

                typingTimers.set(userId, timer);
              }
            }
          } catch {
            // Ignore parse errors
          }
        };

        ws.onclose = () => {
          if (isUnmountedRef.current || wsRef.current !== ws) return;
          setIsConnected(false);

          // Auto-reconnect with exponential backoff if not unmounted
          if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
            const delay = getReconnectDelay(reconnectAttemptsRef.current);
            reconnectAttemptsRef.current += 1;
            reconnectTimerRef.current = setTimeout(() => {
              reconnectTimerRef.current = null;
              connect();
            }, delay);
          }
        };

        ws.onerror = () => {
          if (isUnmountedRef.current || wsRef.current !== ws) return;
          try {
            ws.close();
          } catch {
            // Ignore
          }
        };
      } catch {
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      typingTimers.forEach((timer) => clearTimeout(timer));
      typingTimers.clear();

      const ws = wsRef.current;
      wsRef.current = null;
      cleanupSocket(ws);
      setIsConnected(false);
      setTypingUsers(new Set());
    };
  }, [conversationId]);

  const broadcastMessage = useCallback(
    (content: string) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "chat.message",
            conversation_id: conversationId,
            content,
          }),
        );
      }
    },
    [conversationId],
  );

  const broadcastTyping = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "chat.typing",
          conversation_id: conversationId,
        }),
      );
    }
  }, [conversationId]);

  return {
    isConnected,
    typingUsers: Array.from(typingUsers),
    broadcastMessage,
    broadcastTyping,
  };
}
