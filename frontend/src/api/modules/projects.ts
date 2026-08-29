import { api } from "../client";
import type { Project } from "@/mocks/seed";

export type ProjectStage = "idea" | "in_development" | "beta" | "launched" | "archived";
export type ApplicationStatus = "pending" | "accepted" | "rejected" | "withdrawn" | "shortlisted" | "interview" | "interviewing";

export interface ExtendedProject extends Project {
  title?: string;
  tagline?: string;
  tags?: string[];
  stage: ProjectStage;
  is_archived?: boolean;
  archived_at?: string | null;
}

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

export interface ProjectDraftResponse extends ExtendedProject {
  is_draft: boolean;
  last_draft_save?: string | null;
}

export type SimilarProjectWarning = {
  id: string;
  title: string;
  slug: string;
  title_similarity: number;
  description_similarity: number;
};

export interface ProjectCloneRequest {
  title?: string;
  tagline?: string;
  description?: string;
  visibility?: string;
  include_milestones?: boolean;
  include_tags?: boolean;
}

export const projectsApi = {
  list: (query?: {
    page?: number;
    limit?: number;
    status?: string;
    q?: string;
    language?: string;
    experience?: string;
    remote?: boolean | string;
    paid?: boolean | string;
    opensource?: boolean | string;
    tech?: string;
  }) => api.get<ExtendedProject[]>("/api/projects", { query }),
  myProjects: () => api.get<ExtendedProject[]>("/api/projects/me/list"),
  listMyProjects: () => api.get<ExtendedProject[]>("/api/projects/me/list"),
  byUser: (userId: string) => api.get<ExtendedProject[]>(`/api/projects/user/${userId}`),
  get: (id: string) => api.get<ExtendedProject>(`/api/projects/${id}`),
  create: (body: Partial<ExtendedProject>) => api.post<ExtendedProject>("/api/projects", body),
  update: (id: string, body: Partial<ExtendedProject>) =>
    api.put<ExtendedProject>(`/api/projects/${id}`, body),
  remove: (id: string) => api.delete<void>(`/api/projects/${id}`),
  generateDescription: (prompt: string) =>
    api.post<{ description: string }>("/api/projects/generate-description", { prompt }),
  apply: (id: string, message: string, role?: string) =>
    api.post<void>(`/api/projects/${id}/apply`, { message, role }),
  trending: () => api.get<ExtendedProject[]>("/api/projects/trending"),
  recommended: () => api.get<ExtendedProject[]>("/api/projects/recommended"),
  createDraft: (body: ProjectDraftData) =>
    api.post<ProjectDraftResponse>("/api/projects/draft", body),
  updateDraft: (id: string, body: Partial<ProjectDraftData>) =>
    api.patch<ProjectDraftResponse>(`/api/projects/${id}/draft`, body),
  publishDraft: (id: string) => api.post<ExtendedProject>(`/api/projects/${id}/publish`),
  checkSimilarity: (body: { title: string; description: string }) =>
    api.post<SimilarProjectWarning[]>("/api/projects/check-similarity", body),
  /** Archive a project while preserving its history and setting read-only mode */
  archive: (id: string) => api.post<ExtendedProject>(`/api/projects/${id}/archive`),
  /** Unarchive a project back to active status */
  unarchive: (id: string) => api.post<ExtendedProject>(`/api/projects/${id}/unarchive`),
  /** Clone an existing project as a template */
  clone: (id: string, body?: ProjectCloneRequest) =>
    api.post<ExtendedProject>(`/api/projects/${id}/clone`, body || {}),
};
