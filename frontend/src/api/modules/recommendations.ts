import { api } from "../client";

export interface TechStackRecommendation {
  name: string;
  category: string;
  reason: string;
}

export interface TechStackResponse {
  project_idea: string;
  recommendations: TechStackRecommendation[];
  summary?: string | null;
}

export const recommendationsApi = {
  recommendTechStack: (projectIdea: string) =>
    api.post<TechStackResponse>("/recommendations/tech-stack", { project_idea: projectIdea }),
  builders: (query?: { project_id?: string; limit?: number }) =>
    api.get<{ results: unknown[] }>("/recommendations/builders", { query }),
};
