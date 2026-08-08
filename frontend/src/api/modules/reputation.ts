import { api } from "../client";

export interface ReputationLog {
  id: string;
  user_id: string;
  action: string;
  points: number;
  description?: string | null;
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
  user_id?: string;
  action: string;
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

  getLeaderboard: async (params?: { skip?: number; limit?: number }): Promise<LeaderboardResponse> => {
    return api.get<LeaderboardResponse>("/api/reputation/leaderboard", { query: params });
  },

  awardReputation: async (data: AwardReputationInput): Promise<ReputationLog> => {
    return api.post<ReputationLog>("/api/reputation/award", data);
  },
};
