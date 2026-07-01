import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { builders, projects, flares } from "@/mocks/seed";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

const tabs = ["Developers", "Projects", "Skills", "Flares"] as const;
type Tab = (typeof tabs)[number];

export const Route = createFileRoute("/_app/search")({
  head: () => ({
    meta: [
      { title: "Search — DevLink" },
      { name: "description", content: "Global search across developers, projects, skills and flares." },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const [q, setQ] = useState("");
  const [tab, setTab] = useState<Tab>("Developers");

  const devs = builders.filter((b) => (b.name + b.skills.join(" ")).toLowerCase().includes(q.toLowerCase()));
  const projs = projects.filter((p) => (p.name + p.stack.join(" ")).toLowerCase().includes(q.toLowerCase()));
  const skillSet = Array.from(new Set(builders.flatMap((b) => b.skills))).filter((s) => s.toLowerCase().includes(q.toLowerCase()));
  const fls = flares.filter((f) => f.content.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search DevLink…"
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-3 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />
      </div>
      <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded px-3 py-1.5 text-[12px] font-medium transition-colors",
              tab === t ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Developers" && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {devs.map((b) => (
            <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
              <Card interactive className="flex items-center gap-3 p-3">
                <Avatar src={b.avatar} alt={b.name} size={40} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold text-foreground">{b.name}</p>
                  <p className="truncate text-[12px] text-muted-foreground">{b.role}</p>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
      {tab === "Projects" && (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {projs.map((p) => (
            <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
              <Card interactive className="p-4">
                <div className="flex items-start gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-xl">{p.icon}</span>
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                    <p className="truncate text-[12px] text-muted-foreground">{p.stack.join(" · ")}</p>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
      {tab === "Skills" && (
        <Card className="p-4">
          <div className="flex flex-wrap gap-2">
            {skillSet.map((s) => <TagChip key={s} className="text-[12px]">{s}</TagChip>)}
          </div>
        </Card>
      )}
      {tab === "Flares" && (
        <div className="space-y-3">
          {fls.map((f) => (
            <Card key={f.id} className="p-4">
              <p className="text-[13px] font-semibold text-foreground">{f.author.name}</p>
              <p className="mt-1 text-[13px] text-foreground">{f.content}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
