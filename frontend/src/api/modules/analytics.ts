import { api } from "../client";

export interface SkillStat {
  name: string;
  count: number;
}

export interface TechnologyStat {
  name: string;
  count: number;
}

export interface CommunityStatsResponse {
  generated_at: string;
  timeframe_days: number;
  total_developers: number;
  active_projects: number;
  teams_formed: number;
  open_opportunities: number;
  contributions_this_month: number;
  new_users_this_month: number;
  most_popular_skills: SkillStat[];
  trending_technologies: TechnologyStat[];
}

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
  quickActions?: unknown[];
}

export const analyticsApi = {
  dashboard: () => api.get<DashboardSnapshot>("/api/analytics/dashboard"),
  profile: () => api.get<unknown>("/api/analytics/profile"),
  projects: () => api.get<unknown>("/api/analytics/projects"),
  communityStats: (days?: number) =>
    api.get<CommunityStatsResponse>(`/api/analytics/community/stats${days ? `?days=${days}` : ""}`),
  requestAnalytics: (days: number) =>
    api.get<RequestAnalytics>(`/api/analytics/requests?days=${days}`),
};

export interface RequestAnalytics {
  timeframe_days: number;
  total_requests: number;
  avg_response_time_ms: number;
  error_rate_pct: number;
  active_users: number;
  rate_limited_requests: number;
  requests_by_endpoint: {
    endpoint: string;
    method: string;
    requests: number;
    avg_response_time_ms: number;
    error_count: number;
    error_rate_pct: number;
  }[];
  daily_trend: { date: string; requests: number; errors: number }[];
}
