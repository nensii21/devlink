import { useQuery } from "@tanstack/react-query";
import { teamMatchService } from "@/services";
import type { MatchWeights, MatchResult } from "@/matching/types";
import type { Builder, Project } from "@/mocks/seed";

const STALE_TIME = 5 * 60 * 1000;

export function useTeamMatch(developerId: string, projectId: string, weights?: MatchWeights) {
  return useQuery<MatchResult>({
    queryKey: ["team-match", developerId, projectId, weights],
    queryFn: () => teamMatchService.calculate(developerId, projectId, weights),
    enabled: !!developerId && !!projectId,
    staleTime: STALE_TIME,
  });
}

export function useBuilderMatch(builder: Builder, project: Project, weights?: MatchWeights) {
  return useQuery<MatchResult>({
    queryKey: ["builder-match", builder.id, project.id, weights],
    queryFn: () => Promise.resolve(teamMatchService.calculateForBuilder(builder, project, weights)),
    staleTime: STALE_TIME,
  });
}

export function useProjectRankings(project: Project, weights?: MatchWeights) {
  return useQuery<Array<{ builder: Builder; match: MatchResult }>>({
    queryKey: ["project-rankings", project.id, weights],
    queryFn: () => Promise.resolve(teamMatchService.rankBuildersForProject(project, weights)),
    staleTime: STALE_TIME,
  });
}
