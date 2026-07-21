import { createFileRoute, Link, useSearch } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { HighlightText } from "@/components/shared/HighlightText";
import { searchService } from "@/services";
import { useDebounce } from "@/hooks/useDebounce";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Search, X, Loader2 } from "lucide-react";

const tabs = ["Developers", "Projects", "Skills", "Flares", "Organizations"] as const;
type Tab = (typeof tabs)[number];

export const Route = createFileRoute("/_app/search")({
  head: () => ({
    meta: [
      { title: "Search — DevLink" },
      {
        name: "description",
        content: "Global search across developers, projects, skills, flares and organizations.",
      },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const urlSearch = useSearch({ strict: false }) as { q?: string };
  const [q, setQ] = useState(urlSearch.q ?? "");
  const [tab, setTab] = useState<Tab>("Developers");
  const debouncedQ = useDebounce(q, 250);

  const { data, isFetching, isError } = useQuery({
    queryKey: ["search-page", debouncedQ],
    queryFn: () => searchService.all(debouncedQ),
    enabled: debouncedQ.trim().length >= 1,
    staleTime: 30_000,
  });

  const results = data?.results;
  const hasQuery = debouncedQ.trim().length >= 1;

  return (
    <div className="space-y-4">
      {/* ----- Search input ----- */}
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search DevLink…"
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-10 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
        {q && (
          <button
            type="button"
            onClick={() => setQ("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* ----- Category tabs ----- */}
      <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded px-3 py-1.5 text-[12px] font-medium transition-colors",
              tab === t
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ----- Loading ----- */}
      {isFetching && (
        <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground">
          <Loader2 size={16} className="animate-spin" />
          Searching…
        </div>
      )}

      {/* ----- Error ----- */}
      {isError && !isFetching && (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          Something went wrong. Please try again.
        </Card>
      )}

      {/* ----- Empty state ----- */}
      {!isFetching && !isError && hasQuery && (!results || data?.total === 0) && (
        <Card className="p-8 text-center">
          <Search size={28} className="mx-auto mb-2 text-muted-foreground/50" />
          <p className="text-sm font-medium text-foreground">No results found</p>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Try searching for a developer name, project title, or skill.
          </p>
        </Card>
      )}

      {/* ----- Initial hint ----- */}
      {!hasQuery && (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          Start typing to search across developers, projects, skills, flares and organizations.
        </Card>
      )}

      {/* ----- Results ----- */}
      {!isFetching && !isError && results && hasQuery && data && data.total > 0 && (
        <>
          {tab === "Developers" && (
            <ResultGrid empty={results.users.length === 0}>
              {results.users.map((b) => (
                <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
                  <Card interactive className="flex items-center gap-3 p-4">
                    <Avatar src={b.profile_image ?? ""} alt={`${b.first_name} ${b.last_name}`} size={40} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-semibold text-foreground">
                        <HighlightText text={`${b.first_name} ${b.last_name}`} query={debouncedQ} />
                      </p>
                      <p className="truncate text-[12px] text-muted-foreground">
                        <HighlightText text={b.headline ?? b.role ?? ""} query={debouncedQ} />
                      </p>
                      {b.bio && (
                        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                          <HighlightText text={b.bio} query={debouncedQ} />
                        </p>
                      )}
                    </div>
                  </Card>
                </Link>
              ))}
            </ResultGrid>
          )}

          {tab === "Projects" && (
            <ResultGrid empty={results.projects.length === 0}>
              {results.projects.map((p) => (
                <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
                  <Card interactive className="p-4">
                    <div className="flex items-start gap-3">
                      <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-sm font-bold text-foreground">
                        {p.title.charAt(0).toUpperCase()}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold text-foreground">
                          <HighlightText text={p.title} query={debouncedQ} />
                        </p>
                        {p.tagline && (
                          <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
                            <HighlightText text={p.tagline} query={debouncedQ} />
                          </p>
                        )}
                        {p.tech_stack && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {p.tech_stack.split(",").slice(0, 4).map((s) => (
                              <TagChip key={s} className="text-[10px]">
                                <HighlightText text={s.trim()} query={debouncedQ} />
                              </TagChip>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </ResultGrid>
          )}

          {tab === "Skills" && (
            <Card className="p-4">
              {results.skills.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No skills found.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {results.skills.map((s) => (
                    <TagChip key={s.id} className="text-[12px]">
                      <HighlightText text={s.name} query={debouncedQ} />
                    </TagChip>
                  ))}
                </div>
              )}
            </Card>
          )}

          {tab === "Flares" && (
            <div className="space-y-4">
              {results.flares.length === 0 ? (
                <Card className="p-8 text-center text-sm text-muted-foreground">
                  No flares found.
                </Card>
              ) : (
                results.flares.map((f) => (
                  <Card key={f.id} className="p-4">
                    <p className="text-[13px] font-semibold text-foreground">
                      <HighlightText text={f.title} query={debouncedQ} />
                    </p>
                    <p className="mt-1 text-[13px] text-foreground">
                      <HighlightText text={f.description} query={debouncedQ} />
                    </p>
                    <p className="mt-1 text-[11px] text-muted-foreground">{f.role}</p>
                  </Card>
                ))
              )}
            </div>
          )}

          {tab === "Organizations" && (
            <ResultGrid empty={results.organizations.length === 0}>
              {results.organizations.map((o) => (
                <Card key={o.id} interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-sm font-bold text-foreground">
                      {o.name.charAt(0).toUpperCase()}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold text-foreground">
                        <HighlightText text={o.name} query={debouncedQ} />
                        {o.verified && <span className="ml-1 text-[10px] text-info">✓</span>}
                      </p>
                      {o.description && (
                        <p className="mt-0.5 line-clamp-2 text-[12px] text-muted-foreground">
                          <HighlightText text={o.description} query={debouncedQ} />
                        </p>
                      )}
                      <p className="mt-0.5 text-[11px] text-muted-foreground">
                        {o.members_count} members
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </ResultGrid>
          )}
        </>
      )}
    </div>
  );
}

function ResultGrid({ children, empty }: { children: React.ReactNode; empty: boolean }) {
  if (empty) {
    return (
      <Card className="p-8 text-center text-sm text-muted-foreground">
        No results in this category.
      </Card>
    );
  }
  return <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">{children}</div>;
}
