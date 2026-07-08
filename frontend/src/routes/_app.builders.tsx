import { createFileRoute, Link, useNavigate, useRouterState, Outlet } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { buildersService } from "@/services";
import type { Builder } from "@/services";
import { Card, TagChip, Avatar, EmptyState } from "@/components/shared/primitives";
import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Search,
  Sparkles,
  Calendar,
  Briefcase,
  ChevronRight,
  Check,
  Bookmark,
  Star,
  Award,
} from "lucide-react";
import { motion } from "framer-motion";

type BuildersSearch = {
  tab?: "discover" | "matches" | "connections";
};

export const Route = createFileRoute("/_app/builders")({
  validateSearch: (search: Record<string, unknown>): BuildersSearch => {
    return {
      tab: (search.tab as "discover" | "matches" | "connections") || "discover",
    };
  },
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

const TARGET_SKILLS = [
  "React",
  "Next.js",
  "TypeScript",
  "Node.js",
  "Python",
  "Figma",
  "Kubernetes",
  "AWS",
  "PostgreSQL",
];

function AIMatchCard({ builder }: { builder: Builder }) {
  const [bookmarked, setBookmarked] = useState(false);

  const displaySkills = builder.skills.slice(0, 3);
  const remainingCount = builder.skills.length - 3;
  const matchPercentage = `${builder.matchScore}%`;
  const experienceText = `${builder.yearsExp} Yrs`;
  const availabilityText = builder.availability.split(" ")[0]; // e.g. "Full-time" or "Part-time"

  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="relative h-full flex flex-col justify-between overflow-hidden rounded-3xl border border-border bg-card shadow-soft hover:shadow-card hover:border-primary/50 transition-all duration-300"
    >
      <div>
        {/* Header Banner */}
        <div className="relative">
          <div className="h-28 w-full bg-gradient-to-tr from-amber-200 via-pink-400 via-purple-600 to-blue-700 rounded-t-2xl" />
          <div className="px-4 -mt-10 flex justify-between items-end">
            <Link
              to="/builders/$builderId"
              params={{ builderId: builder.id }}
              className="relative block"
            >
              <img
                src={builder.avatar}
                alt={builder.name}
                className="w-20 h-20 rounded-full border-4 border-card bg-muted object-cover shadow-sm hover:opacity-95 transition-opacity"
              />
              <span className="absolute bottom-1 right-1 block h-3.5 w-3.5 rounded-full bg-success border-2 border-card" />
            </Link>
          </div>
        </div>

        {/* Profile Name, Role & Bookmark */}
        <div className="px-4 pt-3 flex justify-between items-start">
          <div className="text-left min-w-0 flex-1">
            <Link
              to="/builders/$builderId"
              params={{ builderId: builder.id }}
              className="block hover:underline"
            >
              <h3 className="font-bold text-foreground text-[20px] leading-tight truncate">
                {builder.name}
              </h3>
            </Link>
            <p className="text-muted-foreground text-[13px] font-medium mt-0.5 truncate">
              {builder.role}
            </p>
          </div>
          <button
            onClick={() => setBookmarked(!bookmarked)}
            className={cn(
              "w-10 h-10 rounded-full border border-border/80 flex items-center justify-center bg-card transition-all duration-200 cursor-pointer shrink-0 ml-2",
              bookmarked
                ? "text-primary border-primary bg-primary/5"
                : "text-muted-foreground hover:text-foreground hover:bg-muted",
            )}
          >
            <Bookmark size={16} fill={bookmarked ? "currentColor" : "none"} />
          </button>
        </div>

        {/* Skill Tags / Matching Skills highlight */}
        <div className="px-4 mt-4 flex flex-wrap gap-1.5 justify-start">
          {displaySkills.map((s: string) => {
            const isMatching = TARGET_SKILLS.includes(s);
            return (
              <span
                key={s}
                className={cn(
                  "rounded-full text-[12px] font-semibold px-3 py-1.5 border transition-colors",
                  isMatching
                    ? "bg-success/10 border-success/20 text-success"
                    : "bg-muted/60 border-border/10 text-foreground/80",
                )}
              >
                {isMatching && (
                  <Check size={10} strokeWidth={3} className="inline-block mr-1 shrink-0 -mt-0.5" />
                )}
                {s}
              </span>
            );
          })}
          {remainingCount > 0 && (
            <span className="w-9 h-9 rounded-full border border-border/80 bg-card text-foreground text-[12px] font-bold flex items-center justify-center shrink-0">
              +{remainingCount}
            </span>
          )}
        </div>

        {/* Stats Divider Grid */}
        <div className="mx-4 mt-5 py-4 border-y border-border/50 grid grid-cols-3 text-center">
          <div>
            <p className="text-[14px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Sparkles size={14} className="text-primary shrink-0" />
              <span>{matchPercentage}</span>
            </p>
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mt-1">
              Match
            </p>
          </div>
          <div className="border-x border-border/50">
            <p className="text-[14px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Briefcase size={14} className="text-primary shrink-0" />
              <span>{experienceText}</span>
            </p>
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mt-1">
              Experience
            </p>
          </div>
          <div>
            <p className="text-[14px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Calendar size={14} className="text-primary shrink-0" />
              <span>{availabilityText}</span>
            </p>
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mt-1">
              Availability
            </p>
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <div className="p-4 pt-0 mt-4">
        <Link
          to="/builders/$builderId"
          params={{ builderId: builder.id }}
          className="block w-full bg-[#111111] hover:bg-black text-white rounded-full py-3 text-[14px] font-bold text-center transition-all duration-200 shadow-sm cursor-pointer hover:shadow"
        >
          View Details
        </Link>
      </div>
    </motion.div>
  );
}

function BuildersPage() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { tab } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const [q, setQ] = useState("");
  const { data = [] } = useQuery({
    queryKey: ["builders", tab],
    queryFn: tab === "matches" ? buildersService.matches : buildersService.list,
  });

  const [connections, setConnections] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem("devlink:connections");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const handleConnect = (id: string) => {
    setConnections((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      localStorage.setItem("devlink:connections", JSON.stringify(next));
      return next;
    });
  };

  const isDetails = pathname.split("/").filter(Boolean).length > 1;

  if (isDetails) {
    return <Outlet />;
  }

  const baseData = tab === "connections" ? data.filter((b) => connections.includes(b.id)) : data;

  const filtered = baseData.filter(
    (b) =>
      b.name.toLowerCase().includes(q.toLowerCase()) ||
      b.skills.some((s) => s.toLowerCase().includes(q.toLowerCase())),
  );

  const tabs = [
    { k: "discover", label: "Discover" },
    { k: "matches", label: "AI Matches" },
    { k: "connections", label: "Connections" },
  ] as const;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">Builders</h1>
        <p className="text-[13px] text-muted-foreground">Find your next collaborator.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
          {tabs.map((t) => (
            <button
              key={t.k}
              onClick={() => navigate({ search: (prev) => ({ ...prev, tab: t.k }) })}
              className={cn(
                "rounded px-2.5 py-1 text-[12px] font-medium transition-colors cursor-pointer",
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

      {filtered.length === 0 ? (
        q !== "" ? (
          <EmptyState
            variant="search"
            title="No builders found"
            desc={`We couldn't find any developers or skills matching "${q}".`}
          />
        ) : tab === "connections" ? (
          <EmptyState
            variant="connections"
            title="No connections yet"
            desc="Start connecting with other builders to collaborate, share flares, and message them."
            action={
              <button
                onClick={() => navigate({ search: (prev) => ({ ...prev, tab: "discover" }) })}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 cursor-pointer"
              >
                Discover builders
              </button>
            }
          />
        ) : (
          <EmptyState
            variant="default"
            title="No builders yet"
            desc="No builders are currently available in this section."
          />
        )
      ) : tab === "matches" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((b) => (
            <AIMatchCard key={b.id} builder={b} />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((b) => {
            const isConnected = connections.includes(b.id);
            return (
              <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
                <Card interactive className="p-4 text-center h-full flex flex-col justify-between">
                  <div>
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
                    <p className="mt-2 text-[12px] font-semibold text-success">
                      {b.matchScore}% Match
                    </p>
                  </div>
                  <div className="mt-3 flex gap-1.5">
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleConnect(b.id);
                      }}
                      className={cn(
                        "flex-1 rounded-md px-2 py-1 text-[11px] font-semibold transition-colors cursor-pointer",
                        isConnected
                          ? "border border-success bg-success/10 text-success hover:bg-destructive/10 hover:border-destructive hover:text-destructive"
                          : "bg-primary text-primary-foreground hover:opacity-90",
                      )}
                    >
                      {isConnected ? "Connected" : "Connect"}
                    </button>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      className="flex-1 rounded-md border border-border px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted cursor-pointer"
                    >
                      Message
                    </button>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
