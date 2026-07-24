import { api } from "../client";

export interface Issue {
  id: string;
  project_id: string;
  author_id: string;
  title: string;
  description: string;
  status: "open" | "in_progress" | "closed" | "duplicate";
  priority: "low" | "medium" | "high" | "critical";
  labels: string | null;
  is_duplicate_checked: boolean;
  created_at: string;
  updated_at: string;
  author?: {
    id: string;
    username: string;
    full_name: string | null;
    avatar: string | null;
  };
}

export interface DuplicateSuggestion {
  id: string;
  source_issue_id: string;
  duplicate_issue_id: string;
  similarity_score: number;
  created_at: string;
  issue?: Issue;
}

export interface DuplicateCheckResponse {
  has_duplicates: boolean;
  suggestions: DuplicateSuggestion[];
  checked_count: number;
  threshold: number;
}

export interface IssueCreateInput {
  title: string;
  description: string;
  priority?: "low" | "medium" | "high" | "critical";
  labels?: string;
}

export interface IssueUpdateInput {
  title?: string;
  description?: string;
  status?: "open" | "in_progress" | "closed" | "duplicate";
  priority?: "low" | "medium" | "high" | "critical";
  labels?: string;
}

export const issuesApi = {
  list: (projectId: string, params?: { status?: string; skip?: number; limit?: number }) =>
    api.get<Issue[]>(`/api/projects/${projectId}/issues`, { query: params }),

  get: (projectId: string, issueId: string) =>
    api.get<Issue & { duplicate_suggestions: DuplicateSuggestion[] }>(
      `/api/projects/${projectId}/issues/${issueId}`,
    ),

  create: (projectId: string, body: IssueCreateInput) =>
    api.post<Issue>(`/api/projects/${projectId}/issues`, body),

  update: (projectId: string, issueId: string, body: IssueUpdateInput) =>
    api.put<Issue>(`/api/projects/${projectId}/issues/${issueId}`, body),

  remove: (projectId: string, issueId: string) =>
    api.delete<void>(`/api/projects/${projectId}/issues/${issueId}`),

  checkDuplicates: (
    projectId: string,
    body: { title: string; description: string; threshold?: number },
  ) => api.post<DuplicateCheckResponse>(`/api/projects/${projectId}/issues/check-duplicates`, body),

  markAsDuplicate: (projectId: string, issueId: string, duplicateOfId: string) =>
    api.post<Issue>(`/api/projects/${projectId}/issues/${issueId}/mark-duplicate/${duplicateOfId}`),
};
