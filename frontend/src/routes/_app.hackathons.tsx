import { createFileRoute, Outlet, useRouterState, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { hackathonsService } from "@/services";
import { Card, TagChip } from "@/components/shared/primitives";
import { Trophy, Users2, Clock, Plus } from "lucide-react";
import { useState } from "react";
import { CreateHackathonDialog } from "@/components/hackathons/CreateHackathonDialog";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/hackathons")({
  head: () => ({
    meta: [
      { title: "Hackathons — DevLink" },
      { name: "description", content: "Discover hackathons, form teams and ship in a weekend." },
    ],
  }),
  component: HackathonsPage,
});

function HackathonsPage() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const [createOpen, setCreateOpen] = useState(false);

  const { data = [], isLoading } = useQuery({
    queryKey: ["hackathons"],
    queryFn: hackathonsService.list,
  });

  if (pathname !== "/hackathons" && pathname !== "/hackathons/") {
    return <Outlet />;
  }

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Hackathons</h1>
          <p className="text-[13px] text-muted-foreground">
            Join a jam, build a team, ship something new.
          </p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
        >
          <Plus size={14} /> New hackathon
        </button>
        <CreateHackathonDialog open={createOpen} onOpenChange={setCreateOpen} />
      </div>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="h-40 animate-pulse" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
            🏆
          </div>
          <p className="text-[14px] font-semibold text-foreground">No hackathons yet</p>
          <p className="mt-1 text-[13px] text-muted-foreground">Be the first to create one.</p>
          <button
            onClick={() => setCreateOpen(true)}
            className="mt-3 text-[13px] font-medium text-primary hover:underline"
          >
            Create hackathon
          </button>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.map((h) => (
            <Link
              key={h.id}
              to="/hackathons/$hackathonId"
              params={{ hackathonId: h.id }}
              className="block"
            >
              <Card interactive className="p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                    🏆
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-semibold text-foreground">{h.name}</p>
                    <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
                      {h.description}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {h.theme && <TagChip>{h.theme}</TagChip>}
                  <TagChip
                    className={cn(
                      h.status === "registration_open"
                        ? "border-success/30 bg-success/10 text-success"
                        : h.status === "in_progress"
                          ? "border-primary/30 bg-primary/10 text-primary"
                          : h.status === "judging"
                            ? "border-warning/30 bg-warning/10 text-warning"
                            : h.status === "completed"
                              ? "border-success/30 bg-success/10 text-success"
                              : "border-border bg-muted text-muted-foreground",
                    )}
                  >
                    {h.status.replace(/_/g, " ")}
                  </TagChip>
                  {h.prize && (
                    <TagChip className="border-warning/30 bg-warning/10 text-warning">
                      {h.prize}
                    </TagChip>
                  )}
                </div>
                <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Clock size={12} /> {formatDate(h.starts_at)}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Users2 size={12} /> {h.min_team_size}–{h.max_team_size} members
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
