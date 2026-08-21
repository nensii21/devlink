import { api } from "../client";

export interface SkillItem {
  id?: string;
  skill_id?: string;
  name: string;
  category?: string;
  level?: "Beginner" | "Intermediate" | "Advanced" | "Expert" | string;
  years_of_experience?: number;
  yearsOfExperience?: number;
}

export interface SkillMatrixResponse {
  skills_by_category: Record<string, SkillItem[]>;
  total_skills: number;
}

export interface SkillSearchResult {
  id: string;
  name: string;
  category?: string;
  slug?: string;
}

export const skillsApi = {
  list: (query?: { skip?: number; limit?: number }) =>
    api.get<SkillSearchResult[]>("/api/skills", { query }),

  search: (keyword: string) =>
    api.get<SkillSearchResult[]>(`/api/skills/search/${encodeURIComponent(keyword.trim())}`),

  getMyMatrix: () => api.get<SkillMatrixResponse>("/api/skills-matrix/me"),

  getUserMatrix: (userId: string) =>
    api.get<SkillMatrixResponse>(`/api/skills-matrix/user/${userId}`),

  updateMyMatrix: (skills: SkillItem[]) =>
    api.put<SkillMatrixResponse>("/api/skills-matrix/me", {
      skills: skills.map((s) => ({
        id: s.id,
        name: s.name.trim(),
        category: s.category || "Languages",
        level: (s.level || "Beginner").toLowerCase(),
        years_of_experience: s.years_of_experience ?? s.yearsOfExperience ?? 0,
      })),
    }),
};
