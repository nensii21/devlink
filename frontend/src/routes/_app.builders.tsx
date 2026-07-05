import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { buildersService } from "@/services";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { EmptySearchState } from "@/components/shared/EmptySearchState";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

type BuilderTab = "discover" | "matches" | "connections";

export const Route = createFileRoute("/_app/builders")({
  head: () => ({
    meta: [
      { title: "Builders — DevLink" },
      {
        name: "description",
        content: "Discover developers by skills, match score and availability.",
      },
    ],
  }),
  component: BuildersPage,
});

function BuildersPage() {
  const [tab, setTab] = useState<BuilderTab>("discover");
  const [q, setQ] = useState("");
  const { data = [] } = useQuery({
    queryKey: ["builders", tab],
    queryFn: tab === "matches" ? buildersService.matches : buildersService.list,
  });

  const filtered = data.filter(
    (b) =>
      b.name.toLowerCase().includes(q.toLowerCase()) ||
      b.skills.some((s) => s.toLowerCase().includes(q.toLowerCase())),
  );

  const tabs = [
    { k: "discover", label: "Discover" },
    { k: "matches", label: "AI Matches" },
    { k: "connections", label: "Connections" },
  ] as const;

  function clearSearch() {
    setQ("");
  }

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Builders</h1>
        <p className="text-[13px] text-muted-foreground">Find your next collaborator.</p>
      </div>

      {/* Tab switcher + search */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
          {tabs.map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={cn(
                "rounded px-2.5 py-1 text-[12px] font-medium transition-colors",
                tab === t.k
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="relative min-w-0 flex-1">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name or skill…"
            className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {/* Builder grid or empty state */}
      {filtered.length === 0 ? (
        <EmptySearchState
          query={q}
          description={
            q
              ? `No builders match "${q}". Try searching by a different name or skill.`
              : "No builders found in this view."
          }
          onReset={q ? clearSearch : undefined}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((b) => (
            <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
              <Card interactive className="p-4 text-center">
                <div className="mx-auto w-fit">
                  <Avatar src={b.avatar} alt={b.name} size={64} online={b.online} />
                </div>
                <p className="mt-2 text-[14px] font-semibold text-foreground">{b.name}</p>
                <p className="text-[12px] text-muted-foreground">{b.role}</p>
                <p className="text-[11px] text-muted-foreground">
                  {b.country} · {b.yearsExp} yrs
                </p>
                <div className="mt-2 flex flex-wrap justify-center gap-1">
                  {b.skills.slice(0, 3).map((s) => (
                    <TagChip key={s}>{s}</TagChip>
                  ))}
                </div>
                <p className="mt-2 text-[12px] font-semibold text-success">{b.matchScore}% Match</p>
                <div className="mt-2 flex gap-1.5">
                  <button className="flex-1 rounded-md bg-primary px-2 py-1 text-[11px] font-semibold text-primary-foreground hover:opacity-90">
                    Connect
                  </button>
                  <button className="flex-1 rounded-md border border-border px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted">
                    Message
                  </button>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
