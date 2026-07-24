import { api } from "../client";
import type { Notification } from "@/mocks/seed";

export const notificationsApi = {
  list: () => api.get<Notification[]>("/api/notifications"),
  markAllRead: () => api.put<void>("/api/notifications/read"),
  remove: (id: string) => api.delete<void>(`/api/notifications/${id}`),
};
