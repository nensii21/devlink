import { api } from "../client";

export interface DashboardSnapshot {
  stats?: unknown[];
  activity?: unknown[];
  builder_requests?: unknown[];
  invite_requests?: unknown[];
  deadlines?: unknown[];
  trending_projects?: unknown[];
  suggested_builders?: unknown[];
  recommendations?: unknown[];
  recent_messages?: unknown[];
  recent_notifications?: unknown[];
  recent_posts?: unknown[];
  bookmarks?: unknown[];
}

export const analyticsApi = {
  dashboard: () => api.get<DashboardSnapshot>("/api/analytics/dashboard"),
  profile: () => api.get<unknown>("/api/analytics/profile"),
  projects: () => api.get<unknown>("/api/analytics/projects"),
};
