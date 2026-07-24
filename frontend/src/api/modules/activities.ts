import { api } from "../client";

export type ActivityType =
  | "user_registered"
  | "profile_updated"
  | "project_created"
  | "project_updated"
  | "project_archived"
  | "project_milestone"
  | "builder_flare_created"
  | "application_submitted"
  | "application_accepted"
  | "application_rejected"
  | "team_invitation"
  | "repository_connected"
  | "followed_user"
  | "message_sent"
  | "comment_created"
  | "discussion_created"
  | "organization_created"
  | "system";

export interface Activity {
  id: string;
  actor_id: string;
  activity_type: ActivityType;
  title: string;
  description?: string;
  target_id?: string;
  target_type?: string;
  metadata?: Record<string, unknown>;
  icon?: string;
  color?: string;
  created_at: string;
}

export const activitiesApi = {
  getFeed: (query?: {
    limit?: number;
    cursor?: string;
    actor_id?: string;
    target_id?: string;
    target_type?: string;
    activity_types?: ActivityType[];
  }) => {
    const params = new URLSearchParams();
    if (query?.limit) params.append("limit", query.limit.toString());
    if (query?.cursor) params.append("cursor", query.cursor);
    if (query?.actor_id) params.append("actor_id", query.actor_id);
    if (query?.target_id) params.append("target_id", query.target_id);
    if (query?.target_type) params.append("target_type", query.target_type);
    if (query?.activity_types) {
      query.activity_types.forEach((type) => params.append("activity_types", type));
    }

    const queryString = params.toString();
    const url = `/api/activities${queryString ? `?${queryString}` : ""}`;
    return api.get<Activity[]>(url);
  },
};
