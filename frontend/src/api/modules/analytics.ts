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

export interface ProfileAnalyticSummaryItem {
  total: number;
  growth_pct: number;
}

export interface ProfileAnalyticsSummary {
  profile_views: ProfileAnalyticSummaryItem;
  search_appearances: ProfileAnalyticSummaryItem;
  connection_requests: ProfileAnalyticSummaryItem;
  repository_clicks: ProfileAnalyticSummaryItem;
  project_clicks: ProfileAnalyticSummaryItem;
}

export interface ProfileAnalyticTrendItem {
  date: string;
  profile_views: number;
  search_appearances: number;
  connection_requests: number;
  repository_clicks: number;
  project_clicks: number;
}

export interface ProfileAnalyticsResponse {
  summary: ProfileAnalyticsSummary;
  trends: ProfileAnalyticTrendItem[];
}

export interface PlatformSocialProofResponse {
  developers: number;
  projects: number;
  teams: number;
  organizations: number;
  hackathons: number;
  last_updated: string;
}

export const analyticsApi = {
  dashboard: () => api.get<DashboardSnapshot>("/api/analytics/dashboard"),
  socialProof: () => api.get<PlatformSocialProofResponse>("/api/analytics/social-proof"),
  profile: () => api.get<ProfileAnalyticsResponse>("/api/analytics/profile"),
  projects: () => api.get<unknown>("/api/analytics/projects"),
  communityStats: (days?: number) =>
    api.get<CommunityStatsResponse>(`/api/analytics/community/stats${days ? `?days=${days}` : ""}`),
  requestAnalytics: (days: number) =>
    api.get<RequestAnalytics>(`/api/analytics/requests?days=${days}`),
  trackClick: (clickType: "repository" | "project", targetUserId: string, entityId?: string) =>
    api.post<{ status: string }>("/api/analytics/profile/click", {
      click_type: clickType,
      target_user_id: targetUserId,
      entity_id: entityId,
    }),
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
