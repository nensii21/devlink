import { api } from "../client";

export interface MetricScore {
  metric: string;
  score: number;
  label: string;
  description: string;
  weight: number;
}

export interface ImprovementSuggestion {
  priority: string;
  category: string;
  title: string;
  description: string;
}

export interface RepositoryInfo {
  stars: number;
  forks: number;
  open_issues: number;
  language: string | null;
  description: string | null;
  default_branch: string;
  last_push: string | null;
  topics: string[];
}

export interface RepositoryQualityResponse {
  repository_url: string;
  owner: string;
  name: string;
  overall_score: number;
  grade: string;
  metrics: MetricScore[];
  suggestions: ImprovementSuggestion[];
  summary: string;
  repository_info: RepositoryInfo;
}

export const repositoryQualityApi = {
  analyze: (repositoryUrl: string) =>
    api.post<RepositoryQualityResponse>("/api/repository-quality/analyze", {
      body: { repository_url: repositoryUrl },
    }),
};
