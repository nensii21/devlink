import type {
  Developer,
  ProjectRequirements,
  MatchResult,
  MatchStrategy,
  MatchWeights,
  ScoreBreakdown,
} from "./types";
import { DEFAULT_MATCH_WEIGHTS, SCORE_BOUNDS } from "./constants";
import { scoreSkills } from "./scoreSkills";
import { scoreExperience } from "./scoreExperience";
import { scoreInterests } from "./scoreInterests";
import { scoreAvailability } from "./scoreAvailability";
import { scoreCollaboration } from "./scoreCollaboration";
import { buildSummary } from "./helpers";
import { clamp } from "./normalize";

function applyWeights(rawScores: ScoreBreakdown, weights: MatchWeights): ScoreBreakdown {
  return {
    skills: Math.round(rawScores.skills * weights.skills),
    experience: Math.round(rawScores.experience * weights.experience),
    interests: Math.round(rawScores.interests * weights.interests),
    availability: Math.round(rawScores.availability * weights.availability),
    collaboration: Math.round(rawScores.collaboration * weights.collaboration),
  };
}

function calculateMatchInternal(
  developer: Developer,
  project: ProjectRequirements,
  weights: MatchWeights,
): MatchResult {
  const skillsResult = scoreSkills(
    developer.skills,
    project.requiredSkills,
    project.preferredSkills,
  );

  const experienceResult = scoreExperience(developer.yearsExp, project.requiredExperienceYears);

  const interestsResult = scoreInterests(developer.interests, project.tags);

  const availabilityResult = scoreAvailability(
    developer.availabilityHoursPerWeek,
    project.requiredAvailabilityHoursPerWeek,
  );

  const collaborationResult = scoreCollaboration(
    developer.id,
    developer.collaborationHistory,
    project.ownerId,
    project.maintainerIds,
    project.orgId,
    project.contributorIds,
  );

  const rawScores: ScoreBreakdown = {
    skills: skillsResult.score,
    experience: experienceResult.score,
    interests: interestsResult.score,
    availability: availabilityResult.score,
    collaboration: collaborationResult.score,
  };

  const weightedScores = applyWeights(rawScores, weights);

  const totalScore = clamp(
    weightedScores.skills +
      weightedScores.experience +
      weightedScores.interests +
      weightedScores.availability +
      weightedScores.collaboration,
    SCORE_BOUNDS.min,
    SCORE_BOUNDS.max,
  );

  const summary = buildSummary(
    skillsResult.reason,
    experienceResult.reason,
    interestsResult.reason,
    availabilityResult.reason,
    collaborationResult.reason,
  );

  return {
    totalScore,
    breakdown: weightedScores,
    summary,
  };
}

export class WeightedMatchStrategy implements MatchStrategy {
  private readonly weights: MatchWeights;

  constructor(weights: MatchWeights = DEFAULT_MATCH_WEIGHTS) {
    this.weights = { ...weights };
  }

  calculate(developer: Developer, project: ProjectRequirements): MatchResult {
    return calculateMatchInternal(developer, project, this.weights);
  }
}

export function calculateMatch(
  developer: Developer,
  project: ProjectRequirements,
  weights: MatchWeights = DEFAULT_MATCH_WEIGHTS,
): MatchResult {
  return calculateMatchInternal(developer, project, weights);
}

export function calculateMatchWithStrategy(
  developer: Developer,
  project: ProjectRequirements,
  strategy: MatchStrategy,
): MatchResult {
  return strategy.calculate(developer, project);
}
