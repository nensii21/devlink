import { api } from "../client";

export interface CandidateSearchQuery {
  role?: string;
  skills?: string[];
  location?: string;
  minExperience?: number;
}

export interface CandidateProfile {
  id: string;
  name: string;
  headline?: string;
  skills: string[];
  experienceYears?: number;
  matchScore?: number;
}

export const recruiterApi = {
  searchCandidates: async (params?: CandidateSearchQuery): Promise<CandidateProfile[]> => {
    return api.get<CandidateProfile[]>("/api/recruiter/candidates", { query: params });
  },

  getCandidateDetails: async (candidateId: string): Promise<CandidateProfile> => {
    return api.get<CandidateProfile>(`/api/recruiter/candidates/${candidateId}`);
  },

  contactCandidate: async (candidateId: string, message: string): Promise<void> => {
    return api.post<void>(`/api/recruiter/candidates/${candidateId}/contact`, { message });
  },
};
