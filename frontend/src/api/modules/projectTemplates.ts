import { api } from "../client";

export interface TemplateAuthor {
  id: string;
  username: string;
  avatar?: string | null;
}

export interface ProjectTemplate {
  id: string;
  title: string;
  slug: string;
  description: string;
  category: string;
  tech_stack: string[];
  features: string[];
  repository_url?: string | null;
  demo_url?: string | null;
  author_id: string;
  author?: TemplateAuthor | null;
  is_featured: boolean;
  is_published: boolean;
  clones_count: number;
  stars_count: number;
  is_favorited: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectTemplateListResponse {
  templates: ProjectTemplate[];
  total: number;
  categories: string[];
}

export interface ProjectTemplateCreateInput {
  title: string;
  description: string;
  category: string;
  tech_stack: string[];
  features: string[];
  repository_url?: string;
  demo_url?: string;
}

export interface ProjectTemplateUpdateInput {
  title?: string;
  description?: string;
  category?: string;
  tech_stack?: string[];
  features?: string[];
  repository_url?: string;
  demo_url?: string;
  is_published?: boolean;
}

export interface ProjectTemplateCloneInput {
  new_project_title?: string;
  description?: string;
}

export const projectTemplatesApi = {
  listTemplates: async (params?: {
    search?: string;
    category?: string;
    tag?: string;
    sort_by?: string;
    skip?: number;
    limit?: number;
  }): Promise<ProjectTemplateListResponse> => {
    return api.get<ProjectTemplateListResponse>("/api/templates", { query: params });
  },

  getTemplate: async (templateId: string): Promise<ProjectTemplate> => {
    return api.get<ProjectTemplate>(`/api/templates/${templateId}`);
  },

  createTemplate: async (data: ProjectTemplateCreateInput): Promise<ProjectTemplate> => {
    return api.post<ProjectTemplate>("/api/templates", data);
  },

  updateTemplate: async (
    templateId: string,
    data: ProjectTemplateUpdateInput
  ): Promise<ProjectTemplate> => {
    return api.patch<ProjectTemplate>(`/api/templates/${templateId}`, data);
  },

  deleteTemplate: async (templateId: string): Promise<void> => {
    await api.delete(`/api/templates/${templateId}`);
  },

  toggleFavorite: async (
    templateId: string
  ): Promise<{ success: boolean; is_favorited: boolean; stars_count: number }> => {
    return api.post<{ success: boolean; is_favorited: boolean; stars_count: number }>(
      `/api/templates/${templateId}/favorite`
    );
  },

  cloneTemplate: async (
    templateId: string,
    data?: ProjectTemplateCloneInput
  ): Promise<{ id: string; title: string; slug: string }> => {
    return api.post<{ id: string; title: string; slug: string }>(
      `/api/templates/${templateId}/clone`,
      data
    );
  },
};
