import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { projectsService } from "@/services";
import { Card, TagChip } from "@/components/shared/primitives";
import { EmptySearchState } from "@/components/shared/EmptySearchState";
import { Star, GitFork, Users2, Plus, Search } from "lucide-react";
import { useState } from "react";

type StatusFilter = "all" | "active" | "planning" | "shipped";

export const Route = createFileRoute("/_app/projects")({
  head: () => ({
    meta: [
      { title: "Projects — DevLink" },
      {
        name: "description",
        content: "Browse and manage your DevLink projects.",
      },
    ],
  }),
  component: ProjectsPage,
});

function ProjectsPage() {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<StatusFilter>("all");
  const { data = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsService.list,
  });

  const filtered = data.filter(
    (p) =>
      (filter === "all" || p.status === filter) &&
      (q === "" || p.name.toLowerCase().includes(q.toLowerCase())),
  );

  function clearFilters() {
    setQ("");
    setFilter("all");
  }

  const hasActiveFilter = q !== "" || filter !== "all";

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Projects</h1>
          <p className="text-[13px] text-muted-foreground">
            Everything you're building, in one place.
          </p>
        </div>
        <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
          <Plus size={14} /> New project
        </button>
      </div>

      {/* Filter bar */}
      <Card className="p-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search projects…"
              className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
            {(["all", "active", "planning", "shipped"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded px-2.5 py-1 text-[12px] font-medium capitalize transition-colors ${
                  filter === f
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Content area */}
      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="h-40 animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptySearchState
          query={q || (filter !== "all" ? filter : undefined)}
          title={filter !== "all" && q === "" ? `No ${filter} projects` : undefined}
          description={
            filter !== "all" && q === ""
              ? `You don't have any ${filter} projects yet. Try a different status filter.`
              : undefined
          }
          actionLabel="Clear filters"
          onReset={hasActiveFilter ? clearFilters : undefined}
        />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <Link
              key={p.id}
              to="/projects/$projectId"
              params={{ projectId: p.id }}
              className="block"
            >
              <Card interactive className="p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                    {p.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-semibold text-foreground">{p.name}</p>
                    <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
                      {p.description}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {p.stack.map((s) => (
                    <TagChip key={s}>{s}</TagChip>
                  ))}
                </div>
                <div className="mt-3">
                  <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>Progress</span>
                    <span>{p.progress}%</span>
                  </div>
                  <div className="h-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full bg-primary" style={{ width: `${p.progress}%` }} />
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Users2 size={12} /> {p.members}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Star size={12} /> {p.stars}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <GitFork size={12} /> {p.forks}
                  </span>
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                      p.status === "active"
                        ? "bg-success/10 text-success"
                        : p.status === "planning"
                          ? "bg-warning/10 text-warning"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {p.status}
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
