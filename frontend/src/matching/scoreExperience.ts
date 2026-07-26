import type { ExperienceScore } from "./types";
import { toScore } from "./normalize";
import { EXPERIENCE_THRESHOLDS } from "./constants";

export function scoreExperience(developerYears: number, requiredYears: number): ExperienceScore {
  if (requiredYears <= 0) {
    return {
      score: toScore(1),
      developerYears,
      requiredYears,
      reason: "No experience requirement specified.",
    };
  }

  const safeYears = Math.max(0, developerYears);
  let rawScore: number;
  let reason: string;

  if (safeYears >= requiredYears) {
    rawScore = EXPERIENCE_THRESHOLDS.meetsScore;
    const excess = safeYears - requiredYears;
    reason =
      excess > 0
        ? `Exceeds requirement by ${excess} year${excess !== 1 ? "s" : ""}.`
        : "Meets the experience requirement.";
  } else {
    const ratio = safeYears / requiredYears;

    if (ratio >= EXPERIENCE_THRESHOLDS.slightlyBelowThreshold) {
      rawScore =
        EXPERIENCE_THRESHOLDS.slightlyBelowScore +
        (ratio - EXPERIENCE_THRESHOLDS.slightlyBelowThreshold) * 2;
      reason = `Slightly below the ${requiredYears}-year requirement.`;
    } else {
      rawScore = EXPERIENCE_THRESHOLDS.farBelowScore * ratio;
      reason = `Significantly below the ${requiredYears}-year requirement.`;
    }
  }

  return {
    score: toScore(rawScore),
    developerYears: safeYears,
    requiredYears,
    reason,
  };
}
