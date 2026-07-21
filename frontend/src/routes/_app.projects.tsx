import { createFileRoute, Outlet, useRouterState } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { projectsService } from "@/services";
import { Card, TagChip } from "@/components/shared/primitives";
import { Star, GitFork, Users2, Plus, Search, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/projects")({
  head: () => ({
    meta: [
      { title: "Projects — DevLink" },
      { name: "description", content: "Browse and manage your DevLink projects." },
    ],
  }),
  component: ProjectsPage,
});

const LANGUAGES = ["JavaScript", "TypeScript", "Python", "Go", "Rust", "Java", "C++"];
const DIFFICULTIES = ["beginner", "intermediate", "advanced"] as const;
const BOOL_FILTERS = [
  "remote",
  "paid",
  "openSource",
  "ai",
  "web",
  "mobile",
  "backend",
  "frontend",
] as const;
type BoolFilter = (typeof BOOL_FILTERS)[number];

const BOOL_LABELS: Record<BoolFilter, string> = {
  remote: "Remote",
  paid: "Paid",
  openSource: "Open Source",
  ai: "AI",
  web: "Web",
  mobile: "Mobile",
  backend: "Backend",
  frontend: "Frontend",
};

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-md border px-2.5 py-1 text-[12px] font-medium transition-colors",
        active
          ? "border-primary bg-primary/10 text-primary"
          : "border-border bg-surface text-muted-foreground hover:border-primary/50 hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

function toggle<T>(set: T[], val: T): T[] {
  return set.includes(val) ? set.filter((v) => v !== val) : [...set, val];
}

function ProjectsPage() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "all" | "recruiting" | "in-progress" | "completed" | "archived"
  >("all");
  const [showFilters, setShowFilters] = useState(false);
  const [langs, setLangs] = useState<string[]>([]);
  const [difficulties, setDifficulties] = useState<string[]>([]);
  const [boolFilters, setBoolFilters] = useState<BoolFilter[]>([]);

  const { data = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsService.list,
  });

  const chipFilterCount = langs.length + difficulties.length + boolFilters.length;
  const hasActiveFilters = q !== "" || statusFilter !== "all" || chipFilterCount > 0;

  if (pathname !== "/projects" && pathname !== "/projects/") {
    return <Outlet />;
  }

  function clearFilters() {
    setQ("");
    setStatusFilter("all");
    setLangs([]);
    setDifficulties([]);
    setBoolFilters([]);
  }

  const filtered = data.filter((p) => {
    if (statusFilter !== "all" && p.status !== statusFilter) return false;
    if (q && !p.name.toLowerCase().includes(q.toLowerCase())) return false;
    if (langs.length > 0 && (!p.language || !langs.includes(p.language))) return false;
    if (difficulties.length > 0 && (!p.difficulty || !difficulties.includes(p.difficulty)))
      return false;
    for (const f of boolFilters) {
      if (!p[f]) return false;
    }
    return true;
  });

  return (
    <div className="space-y-4">
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

      <Card className="p-4">
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
            {(["all", "recruiting", "in-progress", "completed", "archived"] as const).map((f) => (
              <button
                key={f
                  .split("-")
                  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(" ")}
                onClick={() => setStatusFilter(f)}
                className={`rounded px-2.5 py-1 text-[12px] font-medium capitalize transition-colors ${
                  statusFilter === f
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-[7px] text-[12px] font-medium transition-colors",
              showFilters || hasActiveFilters
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-surface text-muted-foreground hover:text-foreground",
            )}
          >
            <SlidersHorizontal size={13} />
            Filters
            {chipFilterCount > 0 && (
              <span className="grid h-4 w-4 place-items-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                {chipFilterCount}
              </span>
            )}
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-[7px] text-[12px] font-medium text-muted-foreground transition-colors hover:border-destructive/50 hover:text-destructive focus:outline-none focus:ring-2 focus:ring-destructive/20"
              aria-label="Clear all active filters"
            >
              <X size={13} />
              Clear filters
            </button>
          )}
        </div>

        {showFilters && (
          <div className="mt-3 space-y-3 border-t border-border pt-3">
            {/* Language */}
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Language
              </p>
              <div className="flex flex-wrap gap-1.5">
                {LANGUAGES.map((lang) => (
                  <FilterChip
                    key={lang}
                    active={langs.includes(lang)}
                    onClick={() => setLangs(toggle(langs, lang))}
                  >
                    {lang}
                  </FilterChip>
                ))}
              </div>
            </div>

            {/* Difficulty */}
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Difficulty
              </p>
              <div className="flex flex-wrap gap-1.5">
                {DIFFICULTIES.map((d) => (
                  <FilterChip
                    key={d}
                    active={difficulties.includes(d)}
                    onClick={() => setDifficulties(toggle(difficulties, d))}
                  >
                    <span className="capitalize">{d}</span>
                  </FilterChip>
                ))}
              </div>
            </div>

            {/* Boolean tags */}
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Tags
              </p>
              <div className="flex flex-wrap gap-1.5">
                {BOOL_FILTERS.map((f) => (
                  <FilterChip
                    key={f}
                    active={boolFilters.includes(f)}
                    onClick={() => setBoolFilters(toggle(boolFilters, f))}
                  >
                    {BOOL_LABELS[f]}
                  </FilterChip>
                ))}
              </div>
            </div>

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-1 text-[12px] font-medium text-muted-foreground hover:text-foreground"
              >
                <X size={12} /> Clear filters
              </button>
            )}
          </div>
        )}
      </Card>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="h-40 animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
            🔍
          </div>
          <p className="text-[14px] font-semibold text-foreground">
            No projects match your filters
          </p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Try adjusting or resetting your filters.
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-3 text-[13px] font-medium text-primary hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <a key={p.id} href={`/projects/${p.id}`} className="block">
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
                  {p.difficulty && (
                    <TagChip
                      className={cn(
                        p.difficulty === "beginner"
                          ? "border-success/30 bg-success/10 text-success"
                          : p.difficulty === "intermediate"
                            ? "border-warning/30 bg-warning/10 text-warning"
                            : "border-destructive/30 bg-destructive/10 text-destructive",
                      )}
                    >
                      {p.difficulty}
                    </TagChip>
                  )}
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
                      p.status === "recruiting"
                        ? "bg-primary/10 text-primary"
                        : p.status === "in-progress"
                          ? "bg-warning/10 text-warning"
                          : p.status === "completed"
                            ? "bg-success/10 text-success"
                            : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {p.status
                      .split("-")
                      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(" ")}
                  </span>
                </div>
              </Card>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
