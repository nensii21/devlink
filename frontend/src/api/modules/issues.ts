import { api } from "../client";

export interface Issue {
  id: string;
  project_id: string;
  author_id: string;
  title: string;
  description: string;
  status: "open" | "in_progress" | "closed" | "duplicate";
  priority: "low" | "medium" | "high" | "critical";
  labels?: string;
  difficulty?: "beginner" | "intermediate" | "advanced" | "expert";
  difficulty_confidence?: number;
  difficulty_manual_override: boolean;
  created_at: string;
  updated_at: string;
}

export interface DifficultyEstimateResponse {
  difficulty: "beginner" | "intermediate" | "advanced" | "expert";
  confidence: number;
  reasoning: string;
}

export const issuesApi = {
  create: (body: {
    project_id: string;
    title: string;
    description: string;
    priority?: string;
    labels?: string;
  }) => api.post<Issue>("/api/issues", body),

  get: (id: string) => api.get<Issue>(`/api/issues/${id}`),

  listByProject: (projectId: string) =>
    api.get<Issue[]>(`/api/issues/project/${projectId}`),

  update: (
    id: string,
    body: Partial<Pick<Issue, "title" | "description" | "status" | "priority" | "labels">>,
  ) => api.patch<Issue>(`/api/issues/${id}`, body),

  estimateDifficulty: (id: string) =>
    api.post<DifficultyEstimateResponse>(`/api/issues/${id}/estimate`),

  overrideDifficulty: (id: string, difficulty: string) =>
    api.patch<Issue>(`/api/issues/${id}/difficulty`, { difficulty }),
};
