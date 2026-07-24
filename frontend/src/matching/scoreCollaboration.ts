import type { CollaborationScore, CollaborationHistory, ID } from "./types";
import { toScore } from "./normalize";
import { hasPreviousCollaboration } from "./helpers";

export function scoreCollaboration(
  developerId: ID,
  collaborationHistory: CollaborationHistory,
  projectOwnerId: ID,
  maintainerIds: ID[],
  orgId: ID | null,
  contributorIds: ID[],
): CollaborationScore {
  const result = hasPreviousCollaboration(
    developerId,
    collaborationHistory,
    projectOwnerId,
    maintainerIds,
    orgId,
    contributorIds,
  );

  if (!result.hasCollaboration) {
    return {
      score: toScore(0),
      hasPreviousCollaboration: false,
      collaborationType: "",
      reason: "No previous collaboration history with this project.",
    };
  }

  return {
    score: toScore(result.bonusValue),
    hasPreviousCollaboration: true,
    collaborationType: result.type,
    reason: `Previously collaborated with project ${result.type}.`,
  };
}
