import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { HighlightText } from "@/components/shared/HighlightText";
import { builders, projects, flares } from "@/mocks/seed";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Search, X, Building2, Rss, History } from "lucide-react";
import { useGlobalSearch } from "@/hooks/useGlobalSearch";

const tabs = ["Developers", "Projects", "Skills", "Posts", "Organizations"] as const;
type Tab = (typeof tabs)[number];

const organizations = [
  {
    id: "devlink-org",
    name: "DevLink",
    description: "The developer portfolio & project collaboration network.",
    hiring: true,
    members_count: 12,
    projects_count: 5,
  },
];

export const Route = createFileRoute("/_app/search")({
  head: () => ({
    meta: [
      { title: "Search — DevLink" },
      {
        name: "description",
        content: "Global search across developers, projects, posts and organizations.",
      },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const {
    query: q,
    setQuery: setQ,
    recentSearches,
    removeHistoryItem,
    clearHistory,
    clear,
  } = useGlobalSearch({ debounceMs: 200 });

  const [tab, setTab] = useState<Tab>("Developers");

  const query = q.toLowerCase();

  const skillSet = useMemo(
    () =>
      Array.from(new Set(builders.flatMap((b) => b.skills))).filter((s) =>
        s.toLowerCase().includes(query),
      ),
    [query],
  );

  const devs = useMemo(
    () => builders.filter((b) => (b.name + " " + b.skills.join(" ")).toLowerCase().includes(query)),
    [query],
  );

  const projs = useMemo(
    () => projects.filter((p) => (p.name + " " + p.stack.join(" ")).toLowerCase().includes(query)),
    [query],
  );

  const posts = useMemo(
    () =>
      flares.filter((f) =>
        (f.author.name + " " + f.content + " " + f.tags.join(" ")).toLowerCase().includes(query),
      ),
    [query],
  );

  const orgs = useMemo(
    () => organizations.filter((o) => (o.name + " " + o.description).toLowerCase().includes(query)),
    [query],
  );

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search DevLink for developers, projects, or skills..."
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-10 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
        {q && (
          <button
            type="button"
            onClick={clear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Recent Search History Section */}
      {!q && recentSearches.length > 0 && (
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-foreground">
              <History size={14} className="text-muted-foreground" />
              <span>Recent Searches</span>
            </div>
            <button
              type="button"
              onClick={clearHistory}
              className="text-[12px] font-medium text-muted-foreground hover:text-destructive transition-colors"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((item) => (
              <div
                key={item.id}
                className="group flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-[12px] text-foreground hover:border-primary/50 transition-colors"
              >
                <button type="button" onClick={() => setQ(item.query)} className="hover:underline">
                  {item.query}
                </button>
                <button
                  type="button"
                  onClick={() => removeHistoryItem(item.id)}
                  className="text-muted-foreground hover:text-destructive opacity-70 group-hover:opacity-100 transition-opacity"
                  aria-label={`Remove ${item.query} from history`}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Filter Tabs */}
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

      {/* Tab Contents */}
      {tab === "Developers" && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {devs.length === 0 ? (
            <EmptyState query={q} label="developers" />
          ) : (
            devs.map((b) => (
              <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
                <Card interactive className="flex items-center gap-3 p-4">
                  <Avatar src={b.avatar} alt={b.name} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-semibold text-foreground">
                      <HighlightText text={b.name} query={q} />
                    </p>
                    <p className="truncate text-[12px] text-muted-foreground">{b.role}</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {b.skills.slice(0, 3).map((s) => (
                        <TagChip key={s} className="text-[10px]">
                          <HighlightText text={s} query={q} />
                        </TagChip>
                      ))}
                    </div>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}

      {tab === "Projects" && (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {projs.length === 0 ? (
            <EmptyState query={q} label="projects" />
          ) : (
            projs.map((p) => (
              <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
                <Card interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-xl">
                      {p.icon}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold text-foreground">
                        <HighlightText text={p.name} query={q} />
                      </p>
                      <div className="mt-0.5 flex flex-wrap gap-1">
                        {p.stack.map((s) => (
                          <TagChip key={s} className="text-[10px]">
                            <HighlightText text={s} query={q} />
                          </TagChip>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}

      {tab === "Skills" && (
        <div className="flex flex-wrap gap-2">
          {skillSet.length === 0 ? (
            <EmptyState query={q} label="skills" />
          ) : (
            skillSet.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => setQ(skill)}
                className="text-left outline-none"
              >
                <TagChip className="cursor-pointer px-3 py-1.5 text-[12px]">
                  <HighlightText text={skill} query={q} />
                </TagChip>
              </button>
            ))
          )}
        </div>
      )}

      {tab === "Posts" && (
        <div className="space-y-4">
          {posts.length === 0 ? (
            <EmptyState query={q} label="posts" />
          ) : (
            posts.map((f) => (
              <Link key={f.id} to="/flares">
                <Card interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="mt-1 text-muted-foreground">
                      <Rss size={14} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-semibold text-foreground">
                        <HighlightText text={f.author.name} query={q} />
                      </p>
                      <p className="mt-1 text-[13px] text-foreground">
                        <HighlightText text={f.content} query={q} />
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {f.tags.map((t) => (
                          <TagChip key={t} className="text-[10px]">
                            <HighlightText text={`#${t}`} query={q} />
                          </TagChip>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}

      {tab === "Organizations" && (
        <div className="grid gap-3 md:grid-cols-2">
          {orgs.length === 0 ? (
            <EmptyState query={q} label="organizations" />
          ) : (
            orgs.map((org) => (
              <Link key={org.id} to="/organizations/$orgId" params={{ orgId: org.id }}>
                <Card interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 grid h-9 w-9 place-items-center rounded-md bg-muted text-muted-foreground">
                      <Building2 size={16} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-[13px] font-semibold text-foreground">
                          <HighlightText text={org.name} query={q} />
                        </p>
                        {org.hiring && (
                          <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">
                            Hiring
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-[12px] text-muted-foreground">
                        <HighlightText text={org.description} query={q} />
                      </p>
                      <p className="mt-2 text-[11px] text-muted-foreground">
                        {org.members_count} members · {org.projects_count} projects
                      </p>
                    </div>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function EmptyState({ query, label }: { query: string; label: string }) {
  return (
    <Card className="col-span-full p-5 text-center text-[13px] text-muted-foreground">
      No {label} found{query ? ` for "${query}"` : ""}.
    </Card>
  );
}
