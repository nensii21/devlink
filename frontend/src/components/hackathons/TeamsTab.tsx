import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Users2, Plus, LogIn, Loader2, Crown } from "lucide-react";
import { toast } from "sonner";
import { Card, EmptyState } from "@/components/shared/primitives";
import { CreateTeamDialog } from "./CreateTeamDialog";
import { hackathonsService } from "@/services";
import type { HackathonTeam } from "@/services";

interface Props {
  hackathonId: string;
  maxTeamSize: number;
}

export function TeamsTab({ hackathonId, maxTeamSize }: Props) {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [joiningId, setJoiningId] = useState<string | null>(null);

  const { data: teams = [], isLoading } = useQuery({
    queryKey: ["hackathon-teams", hackathonId],
    queryFn: () => hackathonsService.getTeams(hackathonId),
  });

  async function handleJoin(team: HackathonTeam) {
    setJoiningId(team.id);
    try {
      await hackathonsService.joinTeam(team.id);
      toast.success(`Joined ${team.name}!`);
      await queryClient.invalidateQueries({ queryKey: ["hackathon-teams", hackathonId] });
    } catch {
      toast.error("Could not join team. You may already be in one.");
    } finally {
      setJoiningId(null);
    }
  }

  async function handleTeamCreated() {
    setCreateOpen(false);
    await queryClient.invalidateQueries({ queryKey: ["hackathon-teams", hackathonId] });
    // Also refresh the stats card on the detail page
    await queryClient.invalidateQueries({ queryKey: ["hackathon", hackathonId] });
  }

  if (isLoading) {
    return (
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
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
          {teams.length === 0
            ? "No teams yet — be the first to create one."
            : `${teams.length} team${teams.length !== 1 ? "s" : ""} · up to ${maxTeamSize} members each`}
        </p>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-[12px] font-semibold text-primary-foreground hover:opacity-90"
        >
          <Plus size={13} /> Create team
        </button>
      </div>

      {/* Empty */}
      {teams.length === 0 ? (
        <Card className="p-10">
          <EmptyState
            title="No teams yet"
            desc="Create a team to start recruiting members."
            icon={Users2}
            action={
              <button
                onClick={() => setCreateOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
              >
                <Plus size={14} /> Create team
              </button>
            }
          />
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {teams.map((team) => (
            <TeamCard
              key={team.id}
              team={team}
              maxTeamSize={maxTeamSize}
              joining={joiningId === team.id}
              onJoin={() => handleJoin(team)}
            />
          ))}
        </div>
      )}

      <CreateTeamDialog
        hackathonId={hackathonId}
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={handleTeamCreated}
      />
    </div>
  );
}

function TeamCard({
  team,
  maxTeamSize,
  joining,
  onJoin,
}: {
  team: HackathonTeam;
  maxTeamSize: number;
  joining: boolean;
  onJoin: () => void;
}) {
  const isFull = team.member_count >= maxTeamSize;

  return (
    <Card interactive className="flex flex-col gap-3 p-4">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-primary-soft text-primary">
          <Users2 size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <p className="truncate text-[14px] font-semibold text-foreground">{team.name}</p>
            {team.member_count === 1 && (
              <Crown size={11} className="shrink-0 text-warning" aria-label="New team" />
            )}
          </div>
          {team.description && (
            <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
              {team.description}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        {/* Member bar */}
        <div className="flex items-center gap-1.5">
          <div
            className="flex gap-0.5"
            role="img"
            aria-label={`${team.member_count} of ${maxTeamSize} spots filled`}
          >
            {Array.from({ length: maxTeamSize }).map((_, i) => (
              <span
                key={i}
                className={`h-2 w-2 rounded-full transition-colors ${
                  i < team.member_count ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
          <span className="text-[11px] text-muted-foreground">
            {team.member_count}/{maxTeamSize}
          </span>
        </div>

        <button
          onClick={onJoin}
          disabled={joining || isFull}
          className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-[11px] font-medium text-foreground transition-colors hover:border-primary hover:bg-primary hover:text-primary-foreground disabled:pointer-events-none disabled:opacity-40"
        >
          {joining ? (
            <Loader2 size={11} className="animate-spin" />
          ) : isFull ? (
            "Full"
          ) : (
            <>
              <LogIn size={11} /> Join
            </>
          )}
        </button>
      </div>
    </Card>
  );
}
