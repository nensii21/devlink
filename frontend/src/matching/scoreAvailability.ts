import type { AvailabilityScore } from "./types";
import { toScore } from "./normalize";

export function scoreAvailability(
  developerHours: number,
  requiredHours: number,
): AvailabilityScore {
  const safeDevHours = Math.max(0, developerHours);
  const safeRequiredHours = Math.max(0, requiredHours);

  if (safeRequiredHours <= 0) {
    return {
      score: toScore(1),
      developerHours: safeDevHours,
      requiredHours: safeRequiredHours,
      reason: "No availability requirement specified.",
    };
  }

  if (safeDevHours >= safeRequiredHours) {
    const ratio = safeDevHours / safeRequiredHours;
    let rawScore: number;
    if (ratio <= 1.2) {
      rawScore = 1;
    } else if (ratio <= 1.5) {
      rawScore = 0.9;
    } else {
      rawScore = 0.8;
    }

    return {
      score: toScore(rawScore),
      developerHours: safeDevHours,
      requiredHours: safeRequiredHours,
      reason: "Availability meets or exceeds requirements.",
    };
  }

  const ratio = safeDevHours / safeRequiredHours;
  let rawScore: number;
  let reason: string;

  if (ratio >= 0.8) {
    rawScore = 0.7 + (ratio - 0.8) * 1.5;
    reason = "Slightly below availability requirement.";
  } else if (ratio >= 0.5) {
    rawScore = 0.4 + (ratio - 0.5) * 1.0;
    reason = "Moderately below availability requirement.";
  } else {
    rawScore = ratio * 0.8;
    reason = "Significantly below availability requirement.";
  }

  return {
    score: toScore(rawScore),
    developerHours: safeDevHours,
    requiredHours: safeRequiredHours,
    reason,
  };
}
