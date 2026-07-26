import { api } from "../client";
import type { MatchResult, MatchWeights } from "@/matching/types";

export interface TeamMatchRequest {
  developerId: string;
  projectId: string;
  weights?: MatchWeights;
}

export interface TeamMatchResponse {
  totalScore: number;
  breakdown: {
    skills: number;
    experience: number;
    interests: number;
    availability: number;
    collaboration: number;
  };
  summary: string[];
}

export const teamMatchApi = {
  calculate: (body: TeamMatchRequest) => api.post<TeamMatchResponse>("/api/team-match", body),
  calculateBulk: (body: { developerIds: string[]; projectId: string; weights?: MatchWeights }) =>
    api.post<TeamMatchResponse[]>("/api/team-match/bulk", body),
};
