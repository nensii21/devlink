import { api } from "../client";

export type TeamActivityType =
  | "member_joined"
  | "member_left"
  | "role_updated"
  | "project_updated"
  | "milestone_completed"
  | "new_discussion"
  | "file_uploaded";

export interface TeamActivityItem {
  id: string;
  project_id: number;
  activity_type: TeamActivityType;
  title: string;
  description?: string;
  actor_name: string;
  actor_avatar?: string;
  metadata_info?: Record<string, unknown>;
  created_at: string;
}

export interface TeamActivityTimelineResponse {
  project_id: number;
  items: TeamActivityItem[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

/**
 * Activity timeline for one project's team.
 *
 * Errors propagate. This used to answer any failure with a five-item timeline
 * of invented people -- "Sarah Connor joined the team", "Uploaded
 * architecture_v2.pdf" -- with avatars and `created_at` computed from
 * `Date.now()`, so the timestamps were always plausibly recent. It even
 * honoured the `activity_type` filter, so filtering the fake timeline worked
 * and made it look more real (#1249).
 *
 * `TeamActivityTimeline` already renders an error panel and a "No activity
 * events found" empty state.
 */
export const getTeamActivityTimeline = async (
  projectId: number,
  page: number = 1,
  limit: number = 10,
  activityType?: string,
): Promise<TeamActivityTimelineResponse> => {
  let url = `/projects/${projectId}/activity-timeline?page=${page}&limit=${limit}`;
  if (activityType) {
    url += `&activity_type=${encodeURIComponent(activityType)}`;
  }

  return api.get<TeamActivityTimelineResponse>(url);
};
