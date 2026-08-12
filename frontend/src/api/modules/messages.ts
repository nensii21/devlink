import { api } from "../client";
import type { Conversation, Message } from "@/mocks/seed";

export const messagesApi = {
  conversations: () => api.get<Conversation[]>("/api/messages"),
  thread: (conversationId: string) => api.get<Message[]>(`/api/messages/${conversationId}`),
  send: (body: {
    conversation_id?: string;
    receiver_id?: string;
    message?: string;
    content?: string;
    type?: string;
    attachment_url?: string;
    attachment_name?: string;
    attachment_size?: number;
    mime_type?: string;
  }) => {
    const payload = {
      ...body,
      content: body.content ?? body.message ?? "",
    };
    return api.post<Message>("/api/messages", payload);
  },
  markRead: (conversationId: string) => api.post<void>(`/api/messages/${conversationId}/read`),
  addReaction: (messageId: string, emoji: string) =>
    api.post<any>(`/api/messages/${messageId}/reactions`, { emoji }),
  removeReaction: (messageId: string, emoji: string) =>
    api.delete<void>(`/api/messages/${messageId}/reactions/${emoji}`),
};
