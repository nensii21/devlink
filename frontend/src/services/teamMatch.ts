import {
  calculateMatch,
  type Developer,
  type ProjectRequirements,
  type MatchResult,
  type MatchWeights,
} from "@/matching";
import { builders as seedBuilders, projects as seedProjects } from "@/mocks/seed";
import type { Builder, Project } from "@/mocks/seed";
import { teamMatchApi, type TeamMatchResponse } from "@/api/modules/teamMatch";
import { isBackendConfigured } from "@/api";

const delay = 120;
const mock = <T>(v: T): Promise<T> => new Promise((r) => setTimeout(() => r(v), delay));

async function withFallback<T>(call: () => Promise<T>, fallback: T): Promise<T> {
  if (!isBackendConfigured()) return mock(fallback);
  try {
    return await call();
  } catch {
    return fallback;
  }
}

function builderToDeveloper(builder: Builder): Developer {
  return {
    id: builder.id,
    name: builder.name,
    handle: builder.handle,
    role: builder.role,
    avatar: builder.avatar,
    country: builder.country,
    yearsExp: builder.yearsExp,
    skills: builder.skills,
    interests: builder.interests,
    availabilityHoursPerWeek: builder.online ? 20 : 10,
    collaborationHistory: {
      previousOwnerIds: [],
      previousMaintainerIds: [],
      previousOrgIds: [],
      previousContributorIds: [],
    },
    online: builder.online,
    bio: builder.bio,
    lastActiveAt: builder.lastActiveAt,
  };
}

function projectToRequirements(project: Project): ProjectRequirements {
  return {
    id: project.id,
    name: project.name,
    description: project.description,
    requiredSkills: project.stack,
    preferredSkills: [],
    tags: [
      ...(project.ai ? ["AI"] : []),
      ...(project.web ? ["Web Dev"] : []),
      ...(project.mobile ? ["Mobile"] : []),
      ...(project.backend ? ["Backend"] : []),
      ...(project.frontend ? ["Frontend"] : []),
    ],
    requiredExperienceYears:
      project.difficulty === "Advanced" ? 4 : project.difficulty === "Intermediate" ? 2 : 1,
    requiredAvailabilityHoursPerWeek: 10,
    ownerId: "owner-1",
    maintainerIds: [],
    orgId: null,
    contributorIds: [],
  };
}

function responseToMatchResult(response: TeamMatchResponse): MatchResult {
  return {
    totalScore: response.totalScore,
    breakdown: response.breakdown,
    summary: response.summary,
  };
}

export const teamMatchService = {
  calculate: (
    developerId: string,
    projectId: string,
    weights?: MatchWeights,
  ): Promise<MatchResult> =>
    withFallback(
      async () => {
        const response = await teamMatchApi.calculate({ developerId, projectId, weights });
        return responseToMatchResult(response);
      },
      calculateMatchLocal(developerId, projectId, weights),
    ),

  calculateForBuilder: (
    builder: Builder,
    project: Project,
    weights?: MatchWeights,
  ): MatchResult => {
    const developer = builderToDeveloper(builder);
    const requirements = projectToRequirements(project);
    return calculateMatch(developer, requirements, weights);
  },

  rankBuildersForProject: (
    project: Project,
    weights?: MatchWeights,
  ): Array<{ builder: Builder; match: MatchResult }> => {
    const requirements = projectToRequirements(project);
    return seedBuilders
      .map((builder) => ({
        builder,
        match: calculateMatch(builderToDeveloper(builder), requirements, weights),
      }))
      .sort((a, b) => b.match.totalScore - a.match.totalScore);
  },
};

function calculateMatchLocal(
  developerId: string,
  projectId: string,
  weights?: MatchWeights,
): MatchResult {
  const builder = seedBuilders.find((b) => b.id === developerId);
  const project = seedProjects.find((p) => p.id === projectId);

  if (!builder || !project) {
    return {
      totalScore: 0,
      breakdown: { skills: 0, experience: 0, interests: 0, availability: 0, collaboration: 0 },
      summary: ["Developer or project not found."],
    };
  }

  const developer = builderToDeveloper(builder);
  const requirements = projectToRequirements(project);
  return calculateMatch(developer, requirements, weights);
}
