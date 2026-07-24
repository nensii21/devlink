import { api } from "../client";

export interface ExportedSkill {
  id: string;
  name: string;
  level: string | null;
  years_of_experience: number;
}

export interface ExportedProject {
  id: string;
  title: string;
  slug: string;
  tagline: string | null;
  description: string;
  stage: string;
  visibility: string;
  tech_stack: string | null;
  repository_url: string | null;
  website_url: string | null;
  team_size: number;
  hiring: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExportedApplication {
  id: string;
  project_id: string;
  status: string;
  message: string | null;
  portfolio_url: string | null;
  github_url: string | null;
  created_at: string;
}

export interface ExportedConnection {
  user_id: string;
  username: string | null;
  full_name: string | null;
  direction: string;
  created_at: string;
}

export interface ExportedMessage {
  id: string;
  conversation_id: string;
  content: string;
  type: string;
  created_at: string;
}

export interface ExportedBookmark {
  id: string;
  project_id: string;
  created_at: string;
}

export interface ExportedOrganization {
  id: string;
  name: string;
  slug: string;
  organization_type: string;
  description: string | null;
  created_at: string;
}

export interface UserExportData {
  exported_at: string;
  profile: Record<string, unknown>;
  skills: ExportedSkill[];
  projects: ExportedProject[];
  project_memberships: Record<string, unknown>[];
  applications: ExportedApplication[];
  connections: ExportedConnection[];
  messages: ExportedMessage[];
  bookmarks: ExportedBookmark[];
  organizations: ExportedOrganization[];
  activities: Record<string, unknown>[];
  notifications: Record<string, unknown>[];
  builder_flares: Record<string, unknown>[];
}

export interface ExportResponse {
  success: boolean;
  data: UserExportData;
}

export const exportApi = {
  exportData: () => api.post<ExportResponse>("/api/users/me/export"),
};
