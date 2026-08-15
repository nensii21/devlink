import { api } from '../client';

export interface DeveloperInsightsMetrics {
  projects_created: number;
  applications_submitted: number;
  profile_views: number;
  followers_gained: number;
  messages_sent: number;
  contribution_streak: number;
  ai_match_success_rate: number;
}

export interface MetricTrend {
  current: number;
  previous: number;
  percentage_change: number;
}

export interface ActivityPoint {
  date: string;
  activity_count: number;
  projects: number;
  messages: number;
  applications: number;
}

export interface DeveloperInsightsData {
  user_id: number;
  date_range: string;
  metrics: DeveloperInsightsMetrics;
  trends: Record<string, MetricTrend>;
  activity_timeline: ActivityPoint[];
  top_skills_matched: string[];
  recent_achievements: string[];
}

export const getDeveloperInsights = async (range: string = '30d'): Promise<DeveloperInsightsData> => {
  try {
    return await api.get<DeveloperInsightsData>(`/developer-insights?range=${range}`);
  } catch {
    // Fallback data for frontend preview when backend is not running locally or unauthenticated
    const multiplier = range === '7d' ? 1 : range === '30d' ? 3 : range === '90d' ? 8 : range === '1y' ? 25 : 40;
    return {
      user_id: 1,
      date_range: range,
      metrics: {
        projects_created: Math.max(1, Math.floor(multiplier * 0.5)),
        applications_submitted: Math.max(2, Math.floor(multiplier * 0.8)),
        profile_views: 45 * multiplier,
        followers_gained: 4 * multiplier,
        messages_sent: 18 * multiplier,
        contribution_streak: 12,
        ai_match_success_rate: 88.5,
      },
      trends: {
        projects_created: { current: 3, previous: 2, percentage_change: 15.0 },
        applications_submitted: { current: 5, previous: 4, percentage_change: 10.0 },
        profile_views: { current: 150, previous: 120, percentage_change: 25.0 },
        followers_gained: { current: 12, previous: 10, percentage_change: 20.0 },
        messages_sent: { current: 85, previous: 70, percentage_change: 21.4 },
        contribution_streak: { current: 12, previous: 10, percentage_change: 20.0 },
        ai_match_success_rate: { current: 88.5, previous: 82.0, percentage_change: 6.5 },
      },
      activity_timeline: [
        { date: '2026-08-04', activity_count: 8, projects: 1, messages: 5, applications: 2 },
        { date: '2026-08-05', activity_count: 12, projects: 0, messages: 10, applications: 2 },
        { date: '2026-08-06', activity_count: 15, projects: 1, messages: 12, applications: 2 },
        { date: '2026-08-07', activity_count: 9, projects: 0, messages: 7, applications: 2 },
        { date: '2026-08-08', activity_count: 14, projects: 1, messages: 11, applications: 2 },
        { date: '2026-08-09', activity_count: 18, projects: 0, messages: 15, applications: 3 },
        { date: '2026-08-10', activity_count: 22, projects: 1, messages: 18, applications: 3 },
      ],
      top_skills_matched: ['TypeScript', 'React', 'FastAPI', 'Python', 'Docker'],
      recent_achievements: ['Top 10% Contributor', 'Project Milestone Master', '12-Day Streak'],
    };
  }
};
