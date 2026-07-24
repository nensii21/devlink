import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { HighlightText } from "@/components/shared/HighlightText";
import { builders, projects, flares } from "@/mocks/seed";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Search, X, Building2, Rss } from "lucide-react";

const tabs = ["Developers", "Projects", "Posts", "Organizations"] as const;
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
        content: "Global search across developers, projects, skills and flares.",
        content: "Global search across developers, projects, posts and organizations.",
      },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const [q, setQ] = useState("");
  const [tab, setTab] = useState<Tab>("Developers");

  const devs = builders.filter((b) =>
    (b.name + b.skills.join(" ")).toLowerCase().includes(q.toLowerCase()),
  );
  const projs = projects.filter((p) =>
    (p.name + p.stack.join(" ")).toLowerCase().includes(q.toLowerCase()),
  );
  const skillSet = Array.from(new Set(builders.flatMap((b) => b.skills))).filter((s) =>
    s.toLowerCase().includes(q.toLowerCase()),
  );
  const fls = flares.filter((f) => f.content.toLowerCase().includes(q.toLowerCase()));
  const query = q.toLowerCase();

  const devs = builders.filter((b) =>
    (b.name + " " + b.skills.join(" ")).toLowerCase().includes(query),
  );

  const projs = projects.filter((p) =>
    (p.name + " " + p.stack.join(" ")).toLowerCase().includes(query),
  );

  const posts = flares.filter((f) =>
    (f.author.name + " " + f.content + " " + f.tags.join(" ")).toLowerCase().includes(query),
  );

  const orgs = organizations.filter((o) =>
    (o.name + " " + o.description).toLowerCase().includes(query),
  );

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search DevLink for developers, projects, or skills..."
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-3 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
      </div>
      
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
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />

        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search DevLink…"
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-3 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
      </div>
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
          {projs.map((p) => (
            <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
              <Card interactive className="p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-xl">
                    {p.icon}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                    <p className="truncate text-[12px] text-muted-foreground">
                      {p.stack.join(" · ")}
                    </p>
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
        <Card className="p-4">
          <div className="flex flex-wrap gap-2">
            {skillSet.map((s) => (
              <TagChip key={s} className="text-[12px]">
                {s}
              </TagChip>
            ))}
          </div>
        </Card>

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
    <Card className="p-5 text-center text-[13px] text-muted-foreground">
      No {label} found{query ? ` for "${query}"` : ""}.
    </Card>
  );
}
