import type { SkillScore } from "./types";
import { normalizeSkills, toScore } from "./normalize";

export function scoreSkills(
  developerSkills: string[],
  requiredSkills: string[],
  preferredSkills: string[],
): SkillScore {
  const devNormalized = new Set(normalizeSkills(developerSkills));
  const reqNormalized = normalizeSkills(requiredSkills);
  const prefNormalized = normalizeSkills(preferredSkills);

  const allProjectSkills = new Set([...reqNormalized, ...prefNormalized]);

  if (allProjectSkills.size === 0) {
    return {
      score: 0,
      matchedCount: 0,
      totalCount: 0,
      matchedSkills: [],
      reason: "No skills required for this project.",
    };
  }

  const matchedRequired: string[] = [];
  const matchedPreferred: string[] = [];

  for (const skill of reqNormalized) {
    if (devNormalized.has(skill)) {
      matchedRequired.push(skill);
    }
  }

  for (const skill of prefNormalized) {
    if (devNormalized.has(skill) && !matchedRequired.includes(skill)) {
      matchedPreferred.push(skill);
    }
  }

  const totalMatched = matchedRequired.length + matchedPreferred.length;
  const totalRequired = reqNormalized.length;
  const totalPreferred = prefNormalized.length;

  let rawScore: number;

  if (totalRequired > 0) {
    const requiredRatio = matchedRequired.length / totalRequired;
    const preferredBonus =
      totalPreferred > 0 ? (matchedPreferred.length / totalPreferred) * 0.3 : 0;
    rawScore = Math.min(requiredRatio + preferredBonus, 1);
  } else if (totalPreferred > 0) {
    rawScore = matchedPreferred.length / totalPreferred;
  } else {
    rawScore = 0;
  }

  const matchedSkills = [...matchedRequired, ...matchedPreferred];
  const score = toScore(rawScore);

  let reason: string;
  if (totalMatched === 0) {
    reason = "No matching skills found.";
  } else if (totalRequired > 0 && matchedRequired.length === totalRequired) {
    reason = `Matched all ${totalRequired} required skills${matchedPreferred.length > 0 ? ` and ${matchedPreferred.length} preferred skills` : ""}.`;
  } else if (totalRequired > 0) {
    reason = `Matched ${matchedRequired.length} of ${totalRequired} required skills${matchedPreferred.length > 0 ? ` and ${matchedPreferred.length} preferred skills` : ""}.`;
  } else {
    reason = `Matched ${matchedPreferred.length} of ${totalPreferred} preferred skills.`;
  }

  return {
    score,
    matchedCount: totalMatched,
    totalCount: totalRequired + totalPreferred,
    matchedSkills,
    reason,
  };
}
