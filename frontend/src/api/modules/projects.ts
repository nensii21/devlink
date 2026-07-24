import { api } from "../client";
import type { Project } from "@/mocks/seed";

export type SimilarProjectWarning = {
  id: string;
  title: string;
  slug: string;
  title_similarity: number;
  description_similarity: number;
};

export const projectsApi = {
  list: (query?: { page?: number; limit?: number; status?: string; q?: string }) =>
    api.get<Project[]>("/api/projects", { query }),
  get: (id: string) => api.get<Project>(`/api/projects/${id}`),
  create: (body: Partial<Project>) => api.post<Project>("/api/projects", body),
  update: (id: string, body: Partial<Project>) => api.put<Project>(`/api/projects/${id}`, body),
  remove: (id: string) => api.delete<void>(`/api/projects/${id}`),
  apply: (id: string, message: string, role?: string) =>
    api.post<void>(`/api/projects/${id}/apply`, { message, role }),
  trending: () => api.get<Project[]>("/api/projects/trending"),
  recommended: () => api.get<Project[]>("/api/projects/recommended"),
  checkSimilarity: (body: { title: string; description: string }) =>
    api.post<SimilarProjectWarning[]>("/api/projects/check-similarity", body),
};
