import { api } from "../client";
import type { Conversation, Message } from "@/mocks/seed";

export const messagesApi = {
  conversations: () => api.get<Conversation[]>("/api/messages"),
  thread: (conversationId: string) =>
    api.get<Message[]>(`/api/messages/${conversationId}`),
  send: (body: { conversation_id?: string; receiver_id?: string; message: string; attachment?: string }) =>
    api.post<Message>("/api/messages", body),
  markRead: (conversationId: string) =>
    api.post<void>(`/api/messages/${conversationId}/read`),
};
