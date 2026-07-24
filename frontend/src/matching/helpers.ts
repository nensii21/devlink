import type { ID, CollaborationHistory } from "./types";
import { COLLABORATION_BONUS } from "./constants";

export function hasPreviousCollaboration(
  developerId: ID,
  history: CollaborationHistory,
  projectOwnerId: ID,
  maintainerIds: ID[],
  orgId: ID | null,
  contributorIds: ID[],
): { hasCollaboration: boolean; type: string; bonusValue: number } {
  if (history.previousOwnerIds.includes(projectOwnerId)) {
    return {
      hasCollaboration: true,
      type: "project owner",
      bonusValue: COLLABORATION_BONUS.ownerBonus,
    };
  }

  const matchedMaintainer = maintainerIds.find((id) => history.previousMaintainerIds.includes(id));
  if (matchedMaintainer) {
    return {
      hasCollaboration: true,
      type: "project maintainer",
      bonusValue: COLLABORATION_BONUS.maintainerBonus,
    };
  }

  if (orgId && history.previousOrgIds.includes(orgId)) {
    return {
      hasCollaboration: true,
      type: "organization",
      bonusValue: COLLABORATION_BONUS.orgBonus,
    };
  }

  const matchedContributor = contributorIds.find((id) =>
    history.previousContributorIds.includes(id),
  );
  if (matchedContributor) {
    return {
      hasCollaboration: true,
      type: "contributor",
      bonusValue: COLLABORATION_BONUS.contributorBonus,
    };
  }

  return { hasCollaboration: false, type: "", bonusValue: 0 };
}

export function buildSummary(
  skillsReason: string,
  experienceReason: string,
  interestsReason: string,
  availabilityReason: string,
  collaborationReason: string,
): string[] {
  const summaries: string[] = [];
  if (skillsReason) summaries.push(skillsReason);
  if (experienceReason) summaries.push(experienceReason);
  if (interestsReason) summaries.push(interestsReason);
  if (availabilityReason) summaries.push(availabilityReason);
  if (collaborationReason) summaries.push(collaborationReason);
  return summaries;
}
