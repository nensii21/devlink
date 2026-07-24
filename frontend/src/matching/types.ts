export type ID = string;

export interface Developer {
  id: ID;
  name: string;
  handle: string;
  role: string;
  avatar: string;
  country: string;
  yearsExp: number;
  skills: string[];
  interests: string[];
  availabilityHoursPerWeek: number;
  collaborationHistory: CollaborationHistory;
  online: boolean;
  bio: string;
  lastActiveAt: string | null;
}

export interface CollaborationHistory {
  previousOwnerIds: ID[];
  previousMaintainerIds: ID[];
  previousOrgIds: ID[];
  previousContributorIds: ID[];
}

export interface ProjectRequirements {
  id: ID;
  name: string;
  description: string;
  requiredSkills: string[];
  preferredSkills: string[];
  tags: string[];
  requiredExperienceYears: number;
  requiredAvailabilityHoursPerWeek: number;
  ownerId: ID;
  maintainerIds: ID[];
  orgId: ID | null;
  contributorIds: ID[];
}

export interface SkillScore {
  score: number;
  matchedCount: number;
  totalCount: number;
  matchedSkills: string[];
  reason: string;
}

export interface ExperienceScore {
  score: number;
  developerYears: number;
  requiredYears: number;
  reason: string;
}

export interface InterestScore {
  score: number;
  matchedCount: number;
  matchedInterests: string[];
  reason: string;
}

export interface AvailabilityScore {
  score: number;
  developerHours: number;
  requiredHours: number;
  reason: string;
}

export interface CollaborationScore {
  score: number;
  hasPreviousCollaboration: boolean;
  collaborationType: string;
  reason: string;
}

export interface ScoreBreakdown {
  skills: number;
  experience: number;
  interests: number;
  availability: number;
  collaboration: number;
}

export interface MatchResult {
  totalScore: number;
  breakdown: ScoreBreakdown;
  summary: string[];
}

export interface CriterionScore {
  score: number;
  reason: string;
}

export interface MatchStrategy {
  calculate(developer: Developer, project: ProjectRequirements): MatchResult;
}

export interface MatchWeights {
  skills: number;
  experience: number;
  interests: number;
  availability: number;
  collaboration: number;
}

export interface CollaborationHistoryInput {
  previousOwnerIds?: ID[];
  previousMaintainerIds?: ID[];
  previousOrgIds?: ID[];
  previousContributorIds?: ID[];
}

export interface DeveloperInput {
  id: ID;
  name: string;
  handle: string;
  role: string;
  avatar: string;
  country: string;
  yearsExp: number;
  skills: string[];
  interests?: string[];
  availabilityHoursPerWeek?: number;
  collaborationHistory?: CollaborationHistoryInput;
  online: boolean;
  bio: string;
  lastActiveAt: string | null;
}

export interface ProjectRequirementsInput {
  id: ID;
  name: string;
  description: string;
  requiredSkills?: string[];
  preferredSkills?: string[];
  tags?: string[];
  requiredExperienceYears?: number;
  requiredAvailabilityHoursPerWeek?: number;
  ownerId: ID;
  maintainerIds?: ID[];
  orgId?: ID | null;
  contributorIds?: ID[];
}
