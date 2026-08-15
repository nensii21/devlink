/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import { createFileRoute } from '@tanstack/react-router';
import { TeamActivityTimeline } from '@/components/team/TeamActivityTimeline';

export const Route = createFileRoute('/_app/projects/$projectId/activity')({
  component: ProjectActivityPage,
});

function ProjectActivityPage() {
  const { projectId } = Route.useParams();
  return (
    <div className="container mx-auto py-8 px-4">
      <TeamActivityTimeline projectId={Number(projectId) || 1} />
    </div>
  );
}
