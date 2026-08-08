import { createFileRoute, Outlet, useRouterState, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { hackathonsService } from "@/services";
import { Card, TagChip, Skeleton } from "@/components/shared/primitives";
import { Trophy, Users2, Clock, Plus } from "lucide-react";
import { useState, useEffect } from "react";
import { CreateHackathonDialog } from "@/components/hackathons/CreateHackathonDialog";
import { cn } from "@/lib/utils";
import { z } from "zod";

export const Route = createFileRoute("/_app/hackathons")({
  head: () => ({
    meta: [
      { title: "Hackathons — DevLink" },
      { name: "description", content: "Discover hackathons, form teams and ship in a weekend." },
    ],
  }),
  validateSearch: z.object({
    create: z.boolean().optional(),
  }),
  component: HackathonsPage,
});

function HackathonsPage() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const navigate = Route.useNavigate();
  const search = Route.useSearch();
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    if (search.create) {
      setCreateOpen(true);
      // Remove query param to keep the URL clean
      navigate({
        search: (prev) => {
          const next = { ...prev };
          delete next.create;
          return next;
        },
        replace: true,
      });
    }
  }, [search.create]);

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
            <Card key={i} className="p-4 flex flex-col justify-between h-[150px]">
              <div>
                <div className="flex items-start gap-3">
                  <Skeleton className="h-10 w-10 shrink-0 rounded-md animate-pulse" />
                  <div className="min-w-0 flex-1 space-y-1.5 pt-0.5">
                    <Skeleton className="h-4 w-2/3 animate-pulse" />
                    <Skeleton className="h-3 w-5/6 animate-pulse" />
                  </div>
                </div>
                <div className="mt-3 flex gap-1">
                  <Skeleton className="h-5 w-14 rounded-full animate-pulse" />
                  <Skeleton className="h-5 w-16 rounded-full animate-pulse" />
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <Skeleton className="h-3.5 w-24 animate-pulse" />
                <Skeleton className="h-3.5 w-28 animate-pulse" />
              </div>
            </Card>
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
