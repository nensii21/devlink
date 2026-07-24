import type { InterestScore } from "./types";
import { normalizeSkills, toScore } from "./normalize";

export function scoreInterests(developerInterests: string[], projectTags: string[]): InterestScore {
  const devNormalized = new Set(normalizeSkills(developerInterests));
  const projNormalized = new Set(normalizeSkills(projectTags));

  if (devNormalized.size === 0 && projNormalized.size === 0) {
    return {
      score: toScore(0),
      matchedCount: 0,
      matchedInterests: [],
      reason: "No interests or tags available for comparison.",
    };
  }

  if (projNormalized.size === 0) {
    return {
      score: toScore(0),
      matchedCount: 0,
      matchedInterests: [],
      reason: "No project tags defined.",
    };
  }

  if (devNormalized.size === 0) {
    return {
      score: toScore(0),
      matchedCount: 0,
      matchedInterests: [],
      reason: "No developer interests defined.",
    };
  }

  const matched: string[] = [];
  for (const interest of devNormalized) {
    if (projNormalized.has(interest)) {
      matched.push(interest);
    }
  }

  const intersectionSize = matched.length;
  const unionSize = devNormalized.size + projNormalized.size - intersectionSize;
  const rawScore = unionSize > 0 ? intersectionSize / unionSize : 0;
  const score = toScore(rawScore);

  let reason: string;
  if (intersectionSize === 0) {
    reason = "No overlapping interests found.";
  } else if (intersectionSize === projNormalized.size && intersectionSize === devNormalized.size) {
    reason = "Perfect interest alignment.";
  } else {
    reason = `${intersectionSize} shared interest${intersectionSize !== 1 ? "s" : ""} found.`;
  }

  return {
    score,
    matchedCount: intersectionSize,
    matchedInterests: matched,
    reason,
  };
}
