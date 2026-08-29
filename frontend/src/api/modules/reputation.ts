import { api } from "../client";

/**
 * The activities that earn reputation.
 *
 * Mirrors `ReputationAction` in `backend/app/schemas/reputation.py`. The
 * backend validates against this set, so an unrecognised string is a 422
 * rather than a silent ten points.
 */
export type ReputationAction =
  | "merged_pull_request"
  | "completed_project"
  | "community_contribution"
  | "helpful_discussion"
  | "profile_completion"
  | "mentor_recognition"
  | "manual_adjustment";

/** Largest magnitude a single adjustment may carry, in either direction. */
export const MAX_POINTS_PER_AWARD = 500;

export interface ReputationLog {
  id: string;
  user_id: string;
  action: string;
  points: number;
  description?: string | null;
  /** The administrator behind a manual adjustment; null when the platform awarded it. */
  granted_by_id?: string | null;
  created_at: string;
}

export interface ReputationSummary {
  user_id: string;
  reputation_score: number;
  rank_tier: string;
  recent_logs: ReputationLog[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  full_name?: string | null;
  avatar_url?: string | null;
  reputation_score: number;
  rank_tier: string;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
}

export interface AwardReputationInput {
  /**
   * The user receiving the adjustment. Required: it used to be optional and
   * default to the caller, which is the shape of a self-service score.
   */
  user_id: string;
  action: ReputationAction;
  /** Omit to use the standard value for the action. Negative values deduct. */
  points?: number;
  description?: string;
}

export const reputationApi = {
  getMyReputation: async (): Promise<ReputationSummary> => {
    return api.get<ReputationSummary>("/api/reputation/me");
  },

  getUserReputation: async (userId: string): Promise<ReputationSummary> => {
    return api.get<ReputationSummary>(`/api/reputation/user/${userId}`);
  },

  getLeaderboard: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<LeaderboardResponse> => {
    return api.get<LeaderboardResponse>("/api/reputation/leaderboard", { query: params });
  },

  /**
   * Adjust a user's reputation. Administrators only -- a non-admin caller gets
   * a 403, and an unauthenticated one a 401.
   */
  awardReputation: async (data: AwardReputationInput): Promise<ReputationLog> => {
    return api.post<ReputationLog>("/api/reputation/award", data);
  },
};
