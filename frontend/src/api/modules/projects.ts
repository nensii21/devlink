import { api } from "../client";
import type { Project } from "@/mocks/seed";

export interface ProjectDraftData {
  title: string;
  slug: string;
  description?: string;
  tagline?: string;
  stage?: string;
  visibility?: string;
  tech_stack?: string;
  repository_url?: string;
  website_url?: string;
  demo_url?: string;
  team_size?: number;
  max_team_size?: number;
  hiring?: boolean;
  logo_url?: string;
  banner_url?: string;
}

export interface ProjectDraftResponse extends Project {
  is_draft: boolean;
  last_draft_save?: string | null;
}

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
  createDraft: (body: ProjectDraftData) =>
    api.post<ProjectDraftResponse>("/api/projects/draft", body),
  updateDraft: (id: string, body: Partial<ProjectDraftData>) =>
    api.patch<ProjectDraftResponse>(`/api/projects/${id}/draft`, body),
  publishDraft: (id: string) => api.post<Project>(`/api/projects/${id}/publish`),
};
