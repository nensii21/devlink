import { useState, useEffect, useRef, useCallback } from "react";

export interface ChatWebSocketEvent {
  type: string;
  conversation_id: string;
  user_id: string;
  content?: string;
}

export function useChatWebSocket(
  conversationId: string,
  currentUserId: string,
  onNewMessage: (msg: unknown) => void,
) {
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!conversationId) return;

    // Use the existing collab endpoint which handles auth via token
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Assuming the token is available or we use a demo token for this prototype.
    // In a real app we would get the actual token from auth context
    const token = localStorage.getItem("devlink_access_token") || "demo-token";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/collab?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // Join the conversation room
        ws.send(JSON.stringify({ type: "chat.join", conversation_id: conversationId }));
      };

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);

          if (msg.type === "chat.message.new" && msg.conversation_id === conversationId) {
            onNewMessage(msg);
          } else if (msg.type === "chat.typing" && msg.conversation_id === conversationId) {
            if (msg.user_id !== currentUserId) {
              setTypingUsers((prev) => {
                const newSet = new Set(prev);
                newSet.add(msg.user_id);
                return newSet;
              });

              // Clear typing indicator after 3 seconds
              setTimeout(() => {
                setTypingUsers((prev) => {
                  const newSet = new Set(prev);
                  newSet.delete(msg.user_id);
                  return newSet;
                });
              }, 3000);
            }
          }
        } catch {
          // Ignore
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
      };

      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.send(JSON.stringify({ type: "chat.leave", conversation_id: conversationId }));
          } catch {
            // Ignore send errors during cleanup
          }
        }
        ws.close();
      };
    } catch {
      setIsConnected(false);
    }
  }, [conversationId, currentUserId, onNewMessage]);

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
