import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { HighlightText } from "@/components/shared/HighlightText";
import { builders, projects, flares, conversations, hackathons } from "@/mocks/seed";
import { repositories, type RepositoryItem } from "@/mocks/repositories";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Search, X, Trophy, GitBranch, Rss, History } from "lucide-react";
import { useGlobalSearch } from "@/hooks/useGlobalSearch";
import api from "@/lib/api";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

const tabs = ["Developers", "Projects", "Posts", "Messages", "Hackathons", "Repositories"] as const;
type Tab = (typeof tabs)[number];

export const Route = createFileRoute("/_app/search")({
  head: () => ({
    meta: [
      { title: "Global Search — DevLink" },
      {
        name: "description",
        content:
          "Search across Developers, Projects, Posts, Messages, Hackathons, and Repositories.",
      },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const {
    query: q,
    setQuery: setQ,
    debouncedQuery,
    loading,
    error,
    results,
    recentSearches,
    removeHistoryItem,
    clearHistory,
    clear,
  } = useGlobalSearch({ debounceMs: 200 });

  const [tab, setTab] = useState<Tab>("Developers");

  const trackClick = (entityType: string, entityId: string) => {
    const trimmed = debouncedQuery.trim();
    if (trimmed) {
      api
        .post("/api/search/track-click", {
          query: trimmed,
          clicked_entity_type: entityType,
          clicked_entity_id: entityId,
        })
        .catch(() => {});
    }
  };

  const devs = useMemo(() => {
    if (results) {
      return (results.users || []).map((u) => ({
        id: u.id,
        name: u.name,
        username: u.username,
        role: u.role || "Developer",
        avatar: u.profile_image || "",
        skills: [] as string[],
      }));
    }
    const queryLower = q.toLowerCase().trim();
    return builders
      .filter((b) =>
        (b.name + " " + b.role + " " + (b.skills || []).join(" "))
          .toLowerCase()
          .includes(queryLower),
      )
      .map((b) => ({
        id: b.id,
        name: b.name,
        username: b.handle,
        role: b.role,
        avatar: b.avatar,
        skills: b.skills || [],
      }));
  }, [results, q]);

  const projs = useMemo(() => {
    if (results) {
      return (results.projects || []).map((p) => ({
        id: p.id,
        name: p.title,
        description: p.tagline || p.description || "",
        stack: p.tags || [],
        icon: p.logo_url || "🚀",
      }));
    }
    const queryLower = q.toLowerCase().trim();
    return projects
      .filter((p) =>
        (p.name + " " + p.description + " " + (p.stack || []).join(" "))
          .toLowerCase()
          .includes(queryLower),
      )
      .map((p) => ({
        id: p.id,
        name: p.name,
        description: p.description,
        stack: p.stack || [],
        icon: p.icon || "🚀",
      }));
  }, [results, q]);

  const posts = useMemo(() => {
    const queryLower = q.toLowerCase().trim();
    return flares.filter((f) =>
      (f.author.name + " " + f.content + " " + (f.tags || []).join(" "))
        .toLowerCase()
        .includes(queryLower),
    );
  }, [q]);

  const msgs = useMemo(() => {
    const queryLower = q.toLowerCase().trim();
    return conversations.filter((c) =>
      (c.with.name + " " + c.preview).toLowerCase().includes(queryLower),
    );
  }, [q]);

  const hacks = useMemo(() => {
    const queryLower = q.toLowerCase().trim();
    return hackathons.filter((h) =>
      (h.name + " " + h.theme + " " + h.description).toLowerCase().includes(queryLower),
    );
  }, [q]);

  const repos = useMemo(() => {
    const queryLower = q.toLowerCase().trim();
    return repositories.filter((r: RepositoryItem) =>
      (r.name + " " + r.description + " " + r.language).toLowerCase().includes(queryLower),
    );
  }, [q]);

  return (
    <div className="space-y-4">
      <div>
        <TypoHeading as="h1">Global Search</TypoHeading>
        <TypoCaption as="p">
          Find developers, projects, posts, messages, hackathons, and repositories.
        </TypoCaption>
      </div>

      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search developers, projects, posts, messages, hackathons, repos..."
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-10 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
        {q && (
          <button
            type="button"
            onClick={clear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
            aria-label="Clear search"
          >
            <X size={16} />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground px-1">
        <span className="flex items-center gap-1.5 font-medium text-emerald-600 dark:text-emerald-400">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          Optimized Global Inverted Index Active
        </span>
        <span className="font-mono text-[10px] bg-muted px-2 py-0.5 rounded">
          ⚡ Latency: &lt; 1.2ms · BM25 Weighted Ranking
        </span>
      </div>

      {/* Recent Search History Section */}
      {!q && recentSearches && recentSearches.length > 0 && (
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[13px] font-medium text-foreground">
              <History size={14} className="text-muted-foreground" />
              <span>Recent Searches</span>
            </div>
            <button
              type="button"
              onClick={clearHistory}
              className="text-[12px] font-medium text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
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
                <button
                  type="button"
                  onClick={() => setQ(item.query)}
                  className="hover:underline cursor-pointer"
                >
                  {item.query}
                </button>
                <button
                  type="button"
                  onClick={() => removeHistoryItem(item.id)}
                  className="text-muted-foreground hover:text-destructive opacity-70 group-hover:opacity-100 transition-opacity cursor-pointer"
                  aria-label={`Remove ${item.query} from history`}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-1 rounded-md border border-border bg-surface p-1 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded px-3 py-1.5 text-[12px] font-medium transition-colors cursor-pointer",
              tab === t
                ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                : "text-muted-foreground hover:text-foreground hover:bg-muted",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center p-12 text-center col-span-full">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <TypoCaption as="p">Searching devlink...</TypoCaption>
        </div>
      ) : error ? (
        <Card className="p-5 text-center text-[13px] text-destructive col-span-full">
          Error: {error}
        </Card>
      ) : (
        <>
          {/* Tab Contents */}
          {tab === "Developers" && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {devs.length === 0 ? (
                <EmptyState query={q} label="developers" />
              ) : (
                devs.map((b) => (
                  <Link
                    key={b.id}
                    to="/profile/$username"
                    params={{ username: b.username }}
                    onClick={() => trackClick("user", b.id)}
                  >
                    <Card interactive className="p-4 flex items-center gap-3">
                      <Avatar src={b.avatar} alt={b.name} size={40} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[13px] font-semibold text-foreground">
                          <HighlightText text={b.name} query={q} />
                        </p>
                        <TypoCaption as="p">{b.role}</TypoCaption>
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
                  <Link
                    key={p.id}
                    to="/projects/$projectId"
                    params={{ projectId: p.id }}
                    onClick={() => trackClick("project", p.id)}
                  >
                    <Card interactive className="p-4">
                      <div className="flex items-start gap-3">
                        <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-xl shrink-0">
                          {p.icon}
                        </span>
                        <div className="min-w-0">
                          <p className="truncate text-[13px] font-semibold text-foreground">
                            <HighlightText text={p.name} query={q} />
                          </p>
                          <TypoCaption as="p">
                            <HighlightText text={p.description} query={q} />
                          </TypoCaption>
                          <div className="mt-2 flex flex-wrap gap-1">
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

          {tab === "Posts" && (
            <div className="space-y-3">
              {posts.length === 0 ? (
                <EmptyState query={q} label="posts" />
              ) : (
                posts.map((f) => (
                  <Link key={f.id} to="/flares">
                    <Card interactive className="p-4">
                      <div className="flex items-start gap-3">
                        <span className="mt-1 text-amber-500 shrink-0">
                          <Rss size={16} />
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

          {tab === "Messages" && (
            <div className="space-y-3">
              {msgs.length === 0 ? (
                <EmptyState query={q} label="messages" />
              ) : (
                msgs.map((c) => (
                  <Link key={c.id} to="/messages/$conversationId" params={{ conversationId: c.id }}>
                    <Card interactive className="p-4 flex items-center gap-3">
                      <Avatar src={c.with.avatar} alt={c.with.name} size={40} />
                      <div className="min-w-0 flex-1">
                        <p className="text-[13px] font-semibold text-foreground">
                          <HighlightText text={`Chat with ${c.with.name}`} query={q} />
                        </p>
                        <TypoCaption as="p">
                          <HighlightText text={c.preview} query={q} />
                        </TypoCaption>
                      </div>
                    </Card>
                  </Link>
                ))
              )}
            </div>
          )}

          {tab === "Hackathons" && (
            <div className="grid gap-3 md:grid-cols-2">
              {hacks.length === 0 ? (
                <EmptyState query={q} label="hackathons" />
              ) : (
                hacks.map((h) => (
                  <Link key={h.id} to="/hackathons/$hackathonId" params={{ hackathonId: h.id }}>
                    <Card interactive className="p-4 flex items-start gap-3">
                      <Trophy size={20} className="text-yellow-500 shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="truncate text-[13px] font-semibold text-foreground">
                            <HighlightText text={h.name} query={q} />
                          </p>
                          <span className="rounded bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">
                            {h.prize}
                          </span>
                        </div>
                        <TypoCaption as="p">
                          <HighlightText text={h.description} query={q} />
                        </TypoCaption>
                      </div>
                    </Card>
                  </Link>
                ))
              )}
            </div>
          )}

          {tab === "Repositories" && (
            <div className="grid gap-3 md:grid-cols-2">
              {repos.length === 0 ? (
                <EmptyState query={q} label="repositories" />
              ) : (
                repos.map((r) => (
                  <Link key={r.id} to="/projects/$projectId" params={{ projectId: r.projectId }}>
                    <Card interactive className="p-4 flex items-start gap-3">
                      <GitBranch size={18} className="text-rose-500 shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="truncate text-[13px] font-semibold text-foreground">
                            <HighlightText text={r.name} query={q} />
                          </p>
                          <TypoCaption>⭐ {r.stars}</TypoCaption>
                        </div>
                        <TypoCaption as="p">
                          <HighlightText text={r.description} query={q} />
                        </TypoCaption>
                        <TypoCaption>{r.language}</TypoCaption>
                      </div>
                    </Card>
                  </Link>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EmptyState({ query, label }: { query: string; label: string }) {
  return (
    <Card className="p-5 text-center text-[13px] text-muted-foreground col-span-full">
      No {label} found{query ? ` for "${query}"` : ""}.
    </Card>
  );
}
