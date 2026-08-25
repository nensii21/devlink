import { api } from "../client";

export interface DailyActivityPoint {
  date: string;
  activity_count: number;
  messages: number;
  tasks_completed: number;
}

export interface ProjectCollaborationMetricsResponse {
  project_id: number;
  active_members: number;
  total_team_size: number;
  avg_response_time_hours: number;
  messages_exchanged: number;
  tasks_completed: number;
  applications_received: number;
  collaboration_score: number;
  daily_activity: DailyActivityPoint[];
}

/**
 * Collaboration metrics for one project.
 *
 * Errors propagate. This used to catch everything and return a fixed object --
 * a collaboration score of 92, 342 messages exchanged and a seven-day chart
 * hardcoded to the week of 2026-08-04 -- so a 401, a 500 or an unreachable
 * backend rendered as somebody's real-looking project metrics (#1249).
 *
 * `ProjectCollaborationMetrics` already had a loading skeleton, an error panel
 * and a Retry button. The catch here is what made them unreachable.
 */
export const getProjectCollaborationMetrics = async (
  projectId: number,
): Promise<ProjectCollaborationMetricsResponse> =>
  api.get<ProjectCollaborationMetricsResponse>(`/projects/${projectId}/collaboration-metrics`);
