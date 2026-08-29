import { createFileRoute, Outlet, useRouterState, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { projectsService } from "@/services";
import { Card, TagChip, SectionHeader, Skeleton } from "@/components/shared/primitives";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Star, GitFork, Users2, Plus, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog";
import { ProjectFilters } from "@/components/projects/ProjectFilters";
import { ProjectInsightsCard } from "@/components/projects/ProjectInsightsCard";
import { useProjectFilters } from "@/hooks/useProjectFilters";
import { cn } from "@/lib/utils";
import { getRecentlyViewedProjectIds } from "@/lib/recentlyViewedProjects";
import { ProjectOverviewCard } from "@/components/projects/ProjectOverviewCard";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { FilterDrawer, FilterSection, type FilterValue } from "@/components/ui/filter-drawer";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

// eslint-disable-next-line react-refresh/only-export-components
export const projectSearchSchema = z.object({
  page: z.number().catch(1).optional(),
  q: z.string().optional(),
  language: z
    .union([z.string(), z.array(z.string())])
    .optional()
    .transform((val) => (Array.isArray(val) ? val : val ? [val] : [])),
  experience: z
    .union([z.string(), z.array(z.string())])
    .optional()
    .transform((val) => (Array.isArray(val) ? val : val ? [val] : [])),
  tech: z
    .union([z.string(), z.array(z.string())])
    .optional()
    .transform((val) => (Array.isArray(val) ? val : val ? [val] : [])),
  remote: z.boolean().optional(),
  paid: z.boolean().optional(),
  opensource: z.boolean().optional(),
  create: z.boolean().optional(),
});

/**
 * The filter drawer speaks in strings because it renders radio-style chips;
 * the search schema speaks in booleans. These two helpers are the translation,
 * and they keep "unset" distinct from "explicitly false" in both directions —
 * collapsing those was why an unset "Paid" filter used to read as "Unpaid".
 */
function booleanToChoice(value: boolean | undefined): string {
  if (value === undefined) return "";
  return value ? "true" : "false";
}

function choiceToBoolean(value: FilterValue): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

/** Normalise a drawer value into the string array the search schema stores. */
function toStringList(value: FilterValue): string[] {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === "string" && value !== "") return [value];
  return [];
}

export const Route = createFileRoute("/_app/projects")({
  head: () => ({
    meta: [
      { title: "Projects — DevLink" },
      { name: "description", content: "Browse and manage your DevLink projects." },
    ],
  }),
  validateSearch: projectSearchSchema,
  component: ProjectsPage,
});

function ProjectsPage() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const navigate = Route.useNavigate();
  const {
    filters,
    setFilters,
    clearFilters,
    hasActiveFilters: hasFilters,
    chipFilterCount,
  } = useProjectFilters();
  const page = filters.page || 1;
  const ITEMS_PER_PAGE = 6;
  const [createOpen, setCreateOpen] = useState(false);
  const [q, setQ] = useState(filters.q || "");

  // Status filter state (keep for now as it's separate from ProjectFilters component)
  const [statusFilter, setStatusFilter] = useState<
    "all" | "recruiting" | "in-progress" | "completed" | "archived"
  >("all");
  const [showFilters, setShowFilters] = useState(false);
  const [recentProjectIds, setRecentProjectIds] = useState<string[]>([]);
  const search = Route.useSearch();

  useEffect(() => {
    setRecentProjectIds(getRecentlyViewedProjectIds());
  }, []);

  useEffect(() => {
    if (search.create) {
      setCreateOpen(true);
      // Remove query param to keep the URL clean
      navigate({
        search: (prev: any) => {
          const next = { ...prev };
          delete next.create;
          return next;
        },
        replace: true,
      });
    }
  }, [search.create, navigate]);

  const { data = [], isLoading } = useQuery({
    queryKey: [
      "projects",
      filters.language,
      filters.experience,
      filters.remote,
      filters.paid,
      filters.opensource,
      filters.tech,
    ],
    queryFn: () =>
      projectsService.list({
        language: filters.language?.length ? filters.language.join(",") : undefined,
        experience: filters.experience?.length ? filters.experience.join(",") : undefined,
        remote: filters.remote,
        paid: filters.paid,
        opensource: filters.opensource,
        tech: filters.tech?.length ? filters.tech.join(",") : undefined,
      }),
  });

  const recentlyViewed = useMemo(
    () =>
      recentProjectIds
        .map((id) => data.find((project) => project.id === id))
        .filter((project): project is NonNullable<typeof project> => Boolean(project)),
    [recentProjectIds, data],
  );

  const hasActiveFilters = q !== "" || statusFilter !== "all" || hasFilters;

  const filtered = useMemo(
    () =>
      data.filter((p) => {
        if (statusFilter !== "all" && p.status !== statusFilter) return false;
        if (q && !p.name.toLowerCase().includes(q.toLowerCase())) return false;
        return true;
      }),
    [data, statusFilter, q],
  );

  if (pathname !== "/projects" && pathname !== "/projects/") {
    return <Outlet />;
  }

  function handleClearAllFilters() {
    setQ("");
    setStatusFilter("all");
    clearFilters();
  }

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginated = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <TypoHeading as="h1">Projects</TypoHeading>
          <TypoCaption as="p">Everything you're building, in one place.</TypoCaption>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
        >
          <Plus size={14} /> New project
        </button>
        <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
      </div>
      {recentlyViewed.length > 0 && (
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <TypoHeading as="h2">Recently Viewed Projects</TypoHeading>
            <TypoCaption>Your latest project visits</TypoCaption>
          </div>

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {recentlyViewed.map((project) => (
              <a key={project.id} href={`/projects/${project.id}`} className="block">
                <Card interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                      {project.icon}
                    </span>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[14px] font-semibold text-foreground">
                        {project.name}
                      </p>
                      <TypoCaption as="p">{project.description}</TypoCaption>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1">
                    {project.stack.slice(0, 3).map((tech) => (
                      <TagChip key={tech}>{tech}</TagChip>
                    ))}
                  </div>
                </Card>
              </a>
            ))}
          </div>
        </section>
      )}
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
              onClick={handleClearAllFilters}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-[7px] text-[12px] font-medium text-muted-foreground transition-colors hover:border-destructive/50 hover:text-destructive focus:outline-none focus:ring-2 focus:ring-destructive/20"
              aria-label="Clear all active filters"
            >
              <X size={13} />
              Clear filters
            </button>
          )}
        </div>

        <FilterDrawer
          open={showFilters}
          onOpenChange={setShowFilters}
          title="Filter Projects"
          description="Filter projects by programming language, experience, type, and tech stack"
          activeCount={chipFilterCount}
          sections={[
            {
              id: "language",
              title: "Language",
              type: "multi",
              options: [
                { label: "JavaScript", value: "JavaScript" },
                { label: "TypeScript", value: "TypeScript" },
                { label: "Python", value: "Python" },
                { label: "Java", value: "Java" },
                { label: "Go", value: "Go" },
                { label: "Rust", value: "Rust" },
              ],
            },
            {
              id: "experience",
              title: "Experience Level",
              type: "select",
              options: [
                { label: "Beginner", value: "beginner" },
                { label: "Intermediate", value: "intermediate" },
                { label: "Advanced", value: "advanced" },
              ],
            },
            {
              id: "remote",
              title: "Work Location",
              type: "single",
              options: [
                { label: "Remote", value: "true" },
                { label: "Onsite", value: "false" },
              ],
            },
            {
              id: "paid",
              title: "Compensation",
              type: "single",
              options: [
                { label: "Paid", value: "true" },
                { label: "Unpaid", value: "false" },
              ],
            },
            {
              id: "opensource",
              title: "Open Source",
              type: "single",
              options: [
                { label: "Yes", value: "true" },
                { label: "No", value: "false" },
              ],
            },
          ]}
          values={{
            language: filters.language ?? [],
            experience: filters.experience?.[0] ?? "",
            remote: booleanToChoice(filters.remote),
            paid: booleanToChoice(filters.paid),
            opensource: booleanToChoice(filters.opensource),
          }}
          onApply={(newValues) => {
            const boolOrUndefined = (v: unknown): boolean | undefined =>
              v === "" || v === undefined ? undefined : v === "true";
            const stringOrUndefined = (v: unknown): string | undefined =>
              typeof v === "string" && v !== "" ? v : undefined;
            setFilters({
              language: Array.isArray(newValues.language)
                ? (newValues.language as string[])
                : stringOrUndefined(newValues.language)
                  ? [newValues.language as string]
                  : [],
              experience: stringOrUndefined(newValues.experience)
                ? [newValues.experience as string]
                : [],
              remote: boolOrUndefined(newValues.remote),
              paid: boolOrUndefined(newValues.paid),
              opensource: boolOrUndefined(newValues.opensource),
            });
          }}
          onReset={clearFilters}
        />
      </Card>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4 flex flex-col justify-between h-[190px]">
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
                  <Skeleton className="h-5 w-12 rounded-full animate-pulse" />
                </div>
              </div>
              <div>
                <div className="mt-2 space-y-1">
                  <div className="flex items-center justify-between">
                    <Skeleton className="h-3 w-10 animate-pulse" />
                    <Skeleton className="h-3 w-8 animate-pulse" />
                  </div>
                  <Skeleton className="h-1 w-full rounded-full animate-pulse" />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex gap-4">
                    <Skeleton className="h-3.5 w-6 animate-pulse" />
                    <Skeleton className="h-3.5 w-6 animate-pulse" />
                    <Skeleton className="h-3.5 w-6 animate-pulse" />
                  </div>
                  <Skeleton className="h-5 w-20 rounded-md animate-pulse" />
                </div>
              </div>
            </Card>
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
          <TypoCaption as="p">Try adjusting or resetting your filters.</TypoCaption>
          {hasActiveFilters && (
            <button
              onClick={handleClearAllFilters}
              className="mt-3 text-[13px] font-medium text-primary hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {paginated.map((p) => (
              <div key={p.id} className="flex flex-col gap-2">
                <ProjectOverviewCard project={p} />
                <ProjectInsightsCard
                  compact
                  projectId={p.id}
                  title={p.name}
                  description={p.description}
                  techStack={p.stack}
                  status={p.status}
                  members={p.members}
                />
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-8 flex justify-center">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      href={`/projects?page=${Math.max(1, page - 1)}`}
                      aria-disabled={page === 1}
                      className={page === 1 ? "pointer-events-none opacity-50" : ""}
                    />
                  </PaginationItem>
                  {Array.from({ length: totalPages }).map((_, i) => (
                    <PaginationItem key={i}>
                      <PaginationLink href={`/projects?page=${i + 1}`} isActive={page === i + 1}>
                        {i + 1}
                      </PaginationLink>
                    </PaginationItem>
                  ))}
                  <PaginationItem>
                    <PaginationNext
                      href={`/projects?page=${Math.min(totalPages, page + 1)}`}
                      aria-disabled={page === totalPages}
                      className={page === totalPages ? "pointer-events-none opacity-50" : ""}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </>
      )}
    </div>
  );
}
