import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { GitBranch, ExternalLink, Plus, Clock, CheckCircle2, XCircle, Eye } from "lucide-react";
import { Card, EmptyState, TagChip } from "@/components/shared/primitives";
import { SubmitProjectDialog } from "./SubmitProjectDialog";
import { hackathonsService } from "@/services";
import type { HackathonSubmission, HackathonTeam } from "@/services";
import { cn } from "@/lib/utils";

interface Props {
  hackathonId: string;
  teams: HackathonTeam[];
}

const STATUS_META: Record<
  HackathonSubmission["status"],
  { label: string; cls: string; icon: React.ReactNode }
> = {
  draft: {
    label: "Draft",
    cls: "border-border bg-muted text-muted-foreground",
    icon: <Clock size={10} />,
  },
  submitted: {
    label: "Submitted",
    cls: "border-primary/30 bg-primary/10 text-primary",
    icon: <CheckCircle2 size={10} />,
  },
  in_review: {
    label: "In review",
    cls: "border-warning/30 bg-warning/10 text-warning",
    icon: <Eye size={10} />,
  },
  accepted: {
    label: "Accepted",
    cls: "border-success/30 bg-success/10 text-success",
    icon: <CheckCircle2 size={10} />,
  },
  rejected: {
    label: "Rejected",
    cls: "border-destructive/30 bg-destructive/10 text-destructive",
    icon: <XCircle size={10} />,
  },
};

export function SubmissionsTab({ hackathonId, teams }: Props) {
  const queryClient = useQueryClient();
  const [submitOpen, setSubmitOpen] = useState(false);

  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ["hackathon-submissions", hackathonId],
    queryFn: () => hackathonsService.getSubmissions(hackathonId),
  });

  async function handleSubmitted() {
    setSubmitOpen(false);
    await queryClient.invalidateQueries({ queryKey: ["hackathon-submissions", hackathonId] });
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <Card key={i} className="h-28 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-[13px] text-muted-foreground">
          {submissions.length === 0
            ? "No submissions yet."
            : `${submissions.length} submission${submissions.length !== 1 ? "s" : ""}`}
        </p>
        {teams.length > 0 && (
          <button
            onClick={() => setSubmitOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-[12px] font-semibold text-primary-foreground hover:opacity-90"
          >
            <Plus size={13} /> Submit project
          </button>
        )}
      </div>

      {/* Empty */}
      {submissions.length === 0 ? (
        <Card className="p-10">
          <EmptyState
            title="No submissions yet"
            desc={
              teams.length > 0
                ? "Submit your project when you're ready."
                : "Join a team first to submit a project."
            }
            icon={GitBranch}
            action={
              teams.length > 0 ? (
                <button
                  onClick={() => setSubmitOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
                >
                  <Plus size={14} /> Submit project
                </button>
              ) : undefined
            }
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {submissions.map((sub) => (
            <SubmissionCard key={sub.id} submission={sub} teams={teams} />
          ))}
        </div>
      )}

      <SubmitProjectDialog
        hackathonId={hackathonId}
        teams={teams}
        open={submitOpen}
        onOpenChange={setSubmitOpen}
        onSubmitted={handleSubmitted}
      />
    </div>
  );
}

function SubmissionCard({
  submission,
  teams,
}: {
  submission: HackathonSubmission;
  teams: HackathonTeam[];
}) {
  const meta = STATUS_META[submission.status];
  const team = teams.find((t) => t.id === submission.team_id);

  return (
    <Card className="p-4">
      <div className="flex min-w-0 items-start gap-3">
        <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-md bg-primary-soft text-primary">
          <GitBranch size={15} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-[14px] font-semibold text-foreground">{submission.title}</h3>
            <TagChip className={cn("inline-flex items-center gap-1", meta.cls)}>
              {meta.icon} {meta.label}
            </TagChip>
          </div>
          {team && <p className="mt-0.5 text-[12px] text-muted-foreground">by {team.name}</p>}
          <p className="mt-1.5 line-clamp-3 text-[13px] text-foreground/80">
            {submission.description}
          </p>
          {(submission.repo_url || submission.demo_url) && (
            <div className="mt-2 flex flex-wrap gap-3">
              {submission.repo_url && (
                <a
                  href={submission.repo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[12px] font-medium text-primary hover:underline"
                >
                  <GitBranch size={11} /> Repo <ExternalLink size={10} />
                </a>
              )}
              {submission.demo_url && (
                <a
                  href={submission.demo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[12px] font-medium text-primary hover:underline"
                >
                  <ExternalLink size={11} /> Demo
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
