import { api } from "../client";

export interface TagSuggestion {
  name: string;
  confidence: number;
}

export interface ProjectTagResponse {
  tags: TagSuggestion[];
}

export interface ProjectTagRequest {
  title: string;
  description: string;
  tech_stack?: string;
}

export const projectTagsApi = {
  generate: (data: ProjectTagRequest) =>
    api.post<ProjectTagResponse>("/api/project-tags", data),
};
