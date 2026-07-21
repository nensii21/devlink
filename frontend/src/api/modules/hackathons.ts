import { api } from "../client";
import type { Hackathon } from "@/mocks/seed";

export const hackathonsApi = {
  list: () => api.get<Hackathon[]>("/api/hackathons"),
  get: (id: string) => api.get<Hackathon>(`/api/hackathons/${id}`),
  create: (body: Partial<Hackathon>) => api.post<Hackathon>("/api/hackathons", body),
  join: (id: string) => api.post<void>(`/api/hackathons/${id}/join`),
};
