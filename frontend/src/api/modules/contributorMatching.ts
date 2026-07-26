import { api } from "../client";

export interface MatchedContributor {
  user_id: string;
  username: string;
  full_name: string;
  avatar?: string;
  headline?: string;
  match_score: number;
  match_reason: string;
  matching_skills: string[];
  availability: boolean;
}

export interface ContributorMatchResponse {
  project_id: string;
  project_title: string;
  matches: MatchedContributor[];
  generated_at: string;
}

export const contributorMatchingApi = {
  match: (projectId: string, limit = 5) =>
    api.post<ContributorMatchResponse>("/api/contributor-matching/match", {
      project_id: projectId,
      limit,
    }),
};
