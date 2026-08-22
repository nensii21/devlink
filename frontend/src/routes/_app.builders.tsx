import {
  createFileRoute,
  Link,
  useNavigate,
  useChildMatches,
  Outlet,
} from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { buildersService } from "@/services";
import type { Builder } from "@/services";
import {
  Card,
  AnimatedCard,
  TagChip,
  Avatar,
  Skeleton,
  EmptyState,
} from "@/components/shared/primitives";
import { HighlightText } from "@/components/shared/HighlightText";
import { LastActive } from "@/components/shared/LastActive";
import { useState, useMemo, useEffect } from "react";
import { cn } from "@/lib/utils";

import {
  ArrowRight,
  Bookmark,
  Briefcase,
  Calendar,
  Check,
  Search,
  Sparkles,
  UsersRound,
  BadgeCheck,
} from "lucide-react";
import { motion } from "framer-motion";
import { containerVariants } from "@/lib/animations";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { useSavedSearches } from "@/stores/useSavedSearches";
import { SaveSearchDialog } from "@/components/shared/SaveSearchDialog";

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
  validateSearch: (search: Record<string, unknown>): { tab?: string; q?: string } => {
    return {
      tab: typeof search.tab === "string" ? search.tab : undefined,
      q: typeof search.q === "string" ? search.q : undefined,
    };
  },
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
  const rawAvailability = (builder as Builder & { availability?: string }).availability;
  const availabilityText = rawAvailability ? rawAvailability.split(" (")[0] : "Full-time";

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="relative h-full flex flex-col justify-between overflow-hidden rounded-xl border border-border bg-card shadow-xs hover:shadow-sm hover:border-primary/50 transition-all duration-300"
    >
      <div>
        {/* Header Banner */}
        <div className="relative">
          <div className="h-16 w-full bg-gradient-to-tr from-amber-200 via-pink-400 via-purple-600 to-blue-700 rounded-t-xl" />
          <div className="px-3.5 -mt-7 flex justify-between items-end">
            <Link
              to="/builders/$builderId"
              params={{ builderId: builder.id }}
              className="relative block"
            >
              <img
                src={builder.avatar}
                alt={builder.name}
                className="w-14 h-14 rounded-full border-2 border-card bg-muted object-cover shadow-xs hover:opacity-95 transition-opacity"
              />
              <span
                className={cn(
                  "absolute bottom-0.5 right-0.5 block h-3 w-3 rounded-full border-2 border-card",
                  builder.online ? "bg-success" : "bg-muted-foreground/40",
                )}
              />
            </Link>
          </div>
        </div>

        {/* Profile Name, Role & Bookmark */}
        <div className="px-3.5 pt-2 flex justify-between items-start">
          <div className="text-left min-w-0 flex-1">
            <Link
              to="/builders/$builderId"
              params={{ builderId: builder.id }}
              className="block hover:underline"
            >
              <TypoSection>
                {builder.name}
                {builder.verified && (
                  <BadgeCheck
                    className={cn(
                      "shrink-0 h-4 w-4",
                      builder.premium
                        ? "text-amber-500 fill-amber-500/10 animate-pulse"
                        : "text-primary",
                    )}
                    aria-label={builder.premium ? "Premium Verified User" : "Verified User"}
                  />
                )}
              </TypoSection>
            </Link>
            <TypoCaption as="p">{builder.role}</TypoCaption>
          </div>
          <button
            type="button"
            aria-label={bookmarked ? "Remove bookmark" : "Bookmark builder"}
            aria-pressed={bookmarked}
            onClick={() => setBookmarked(!bookmarked)}
            className={cn(
              "w-8 h-8 rounded-full border border-border/80 flex items-center justify-center bg-card transition-all duration-200 cursor-pointer shrink-0 ml-2",
              bookmarked
                ? "text-primary border-primary bg-primary/5"
                : "text-muted-foreground hover:text-foreground hover:bg-muted",
            )}
          >
            <Bookmark size={14} fill={bookmarked ? "currentColor" : "none"} />
          </button>
        </div>

        {/* Skill Tags / Matching Skills highlight */}
        <div className="px-3.5 mt-2.5 flex flex-wrap gap-1 justify-start">
          {displaySkills.map((s: string) => {
            const isMatching = TARGET_SKILLS.includes(s);
            return (
              <span
                key={s}
                className={cn(
                  "rounded-full text-[11px] font-semibold px-2.5 py-1 border transition-colors",
                  isMatching
                    ? "bg-success/10 border-success/20 text-success"
                    : "bg-muted/60 border-border/10 text-foreground/80",
                )}
              >
                {isMatching && (
                  <Check size={9} strokeWidth={3} className="inline-block mr-1 shrink-0 -mt-0.5" />
                )}
                {s}
              </span>
            );
          })}
          {remainingCount > 0 && (
            <span className="h-7 w-7 rounded-full border border-border/80 bg-card text-foreground text-[11px] font-bold flex items-center justify-center shrink-0">
              +{remainingCount}
            </span>
          )}
        </div>

        {/* Stats Divider Grid */}
        <div className="mx-3.5 mt-3 py-2.5 border-y border-border/50 grid grid-cols-3 text-center">
          <div>
            <p className="text-[13px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Sparkles size={13} className="text-primary shrink-0" />
              <span>{matchPercentage}</span>
            </p>
            <TypoCaption as="p">Match</TypoCaption>
          </div>
          <div className="border-x border-border/50">
            <p className="text-[13px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Briefcase size={13} className="text-primary shrink-0" />
              <span>{experienceText}</span>
            </p>
            <TypoCaption as="p">Experience</TypoCaption>
          </div>
          <div>
            <p className="text-[13px] font-bold text-foreground flex items-center justify-center gap-0.5">
              <Calendar size={13} className="text-primary shrink-0" />
              <span>{availabilityText}</span>
            </p>
            <TypoCaption as="p">Availability</TypoCaption>
          </div>
        </div>
      </div>

      {/* CTA Button */}
      <div className="p-3.5 pt-0 mt-3">
        <Link
          to="/builders/$builderId"
          params={{ builderId: builder.id }}
          className="block w-full bg-[#111111] hover:bg-black text-white rounded-full py-2 text-[13px] font-bold text-center transition-all duration-200 shadow-xs cursor-pointer hover:shadow"
        >
          View Details
        </Link>
      </div>
    </motion.div>
  );
}

function BuilderRecommendationsEmptyState({ onExplore }: { onExplore: () => void }) {
  return (
    <section
      className="relative overflow-hidden rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/10 via-card to-card px-4 py-8 text-center shadow-xs sm:px-8"
      aria-labelledby="builder-recommendations-empty-title"
    >
      <div className="pointer-events-none absolute -left-12 top-0 h-36 w-36 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -right-8 h-44 w-44 rounded-full bg-violet-500/10 blur-3xl" />
      <div className="relative mx-auto flex max-w-md flex-col items-center">
        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-card">
          <Sparkles size={28} aria-hidden="true" />
          <span className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full border-4 border-card bg-violet-500 text-white">
            <UsersRound size={13} aria-hidden="true" />
          </span>
        </div>
        <p className="mt-6 text-xs font-bold uppercase tracking-[0.18em] text-primary">
          AI-powered matches
        </p>
        <h2
          id="builder-recommendations-empty-title"
          className="mt-2 text-xl font-bold tracking-tight text-foreground sm:text-2xl"
        >
          We’re finding your best collaborators
        </h2>
        <TypoCaption as="p">
          We don’t have a recommendation for you yet. Explore the community to discover builders who
          share your interests and skills.
        </TypoCaption>
        <button
          type="button"
          onClick={onExplore}
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-transform hover:-translate-y-0.5 hover:shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          Explore builders
          <ArrowRight size={16} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}

function BuildersPage() {
  const childMatches = useChildMatches();
  const search = Route.useSearch();
  const tab = search.tab;
  const navigate = useNavigate({ from: Route.fullPath });
  const [q, setQ] = useState(search.q || "");
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const saveSearch = useSavedSearches((s) => s.saveSearch);

  useEffect(() => {
    if (search.q !== undefined) {
      setQ(search.q);
    }
  }, [search.q]);

  useEffect(() => {
    const handler = setTimeout(() => {
      navigate({
        search: (prev: any) => ({ ...prev, q: q || undefined }),
        replace: true,
      });
    }, 300);
    return () => clearTimeout(handler);
  }, [q, navigate]);
  const { data = [], isLoading } = useQuery({
    queryKey: ["builders", tab],
    queryFn: () => (tab === "matches" ? buildersService.matches() : buildersService.list()),
  });

  const [connections, setConnections] = useState<string[]>(() => {
    if (typeof window === "undefined") return [];
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

  const baseData = useMemo(
    () => (tab === "connections" ? data.filter((b) => connections.includes(b.id)) : data),
    [data, tab, connections],
  );

  const filtered = useMemo(
    () =>
      baseData.filter(
        (b) =>
          b.name.toLowerCase().includes(q.toLowerCase()) ||
          b.skills.some((s) => s.toLowerCase().includes(q.toLowerCase())),
      ),
    [baseData, q],
  );

  if (childMatches.length > 0) {
    return <Outlet />;
  }

  const tabs = [
    { k: "discover", label: "Discover" },
    { k: "matches", label: "AI Matches" },
    { k: "connections", label: "Connections" },
  ] as const;

  return (
    <div className="space-y-4">
      <div>
        <TypoHeading as="h1">Builders</TypoHeading>
        <TypoCaption as="p">Find your next collaborator.</TypoCaption>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
          {tabs.map((t) => (
            <button
              key={t.k}
              type="button"
              onClick={() => navigate({ search: (prev: any) => ({ ...prev, tab: t.k }) })}
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
            placeholder="Search by builder name or skill..."
            className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <button
          onClick={() => setSaveDialogOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-[7px] text-[12px] font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <Bookmark size={13} />
          Save Search
        </button>
      </div>

      <SaveSearchDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onSave={(name) => {
          saveSearch({
            name,
            type: "Developers",
            query: q,
            tab,
          } as any);
        }}
      />

      <motion.div
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        role="status"
        aria-busy={isLoading || undefined}
      >
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="p-4 text-center">
              <div className="mx-auto w-fit">
                <Skeleton className="h-16 w-16 shrink-0 rounded-full" />
              </div>
              <Skeleton className="mx-auto mt-2 h-4 w-28" />
              <Skeleton className="mx-auto mt-1 h-3 w-20" />
              <Skeleton className="mx-auto mt-1 h-3 w-36" />
              <div className="mt-2 flex flex-wrap justify-center gap-1">
                <Skeleton className="h-5 w-14" />
                <Skeleton className="h-5 w-12" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="mx-auto mt-2 h-3 w-20" />
              <div className="mt-2 flex gap-1.5">
                <Skeleton className="h-7 flex-1" />
                <Skeleton className="h-7 flex-1" />
              </div>
            </Card>
          ))
        ) : filtered.length === 0 && tab === "matches" && !q ? (
          <div className="col-span-full">
            <BuilderRecommendationsEmptyState
              onExplore={() => navigate({ search: (prev: any) => ({ ...prev, tab: "discover" }) })}
            />
          </div>
        ) : filtered.length === 0 ? (
          <div className="col-span-full">
            <EmptyState
              title={tab === "connections" ? "No connections yet" : "No builders found"}
              desc={
                tab === "connections"
                  ? "Connect with builders to keep track of potential collaborators here."
                  : "Try adjusting your search filters or explore more builders."
              }
              illustration="no-results"
            />
          </div>
        ) : tab === "matches" ? (
          filtered.map((b) => <AIMatchCard key={b.id} builder={b} />)
        ) : (
          filtered.map((b, i) => {
            const isConnected = connections.includes(b.id);
            return (
              <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
                <AnimatedCard
                  interactive
                  index={i}
                  className="p-4 text-center h-full flex flex-col justify-between"
                >
                  <div>
                    <div className="mx-auto w-fit">
                      <Avatar src={b.avatar} alt={b.name} size={64} online={b.online} />
                    </div>
                    <p className="mt-2 text-[14px] font-semibold text-foreground flex items-center justify-center gap-1">
                      <HighlightText text={b.name} query={q} />
                      {b.verified && (
                        <BadgeCheck
                          className={cn(
                            "h-3.5 w-3.5 shrink-0",
                            b.premium
                              ? "text-amber-500 fill-amber-500/10 animate-pulse"
                              : "text-primary",
                          )}
                          aria-label={b.premium ? "Premium Verified User" : "Verified User"}
                        />
                      )}
                    </p>
                    <TypoCaption as="p">
                      <HighlightText text={b.role} query={q} />
                    </TypoCaption>
                    <TypoCaption as="p">
                      {b.country} · {b.yearsExp} yrs
                    </TypoCaption>
                    <LastActive lastActiveAt={b.lastActiveAt} className="mt-1 justify-center" />
                    <div className="mt-2 flex flex-wrap justify-center gap-1">
                      {b.skills.slice(0, 3).map((s) => (
                        <TagChip key={s}>
                          <HighlightText text={s} query={q} />
                        </TagChip>
                      ))}
                    </div>
                    {b.matchScore && (
                      <p className="mt-2 text-[12px] font-semibold text-success">
                        {b.matchScore}% Match
                      </p>
                    )}
                  </div>
                  <div className="mt-3 flex gap-1.5">
                    <button
                      type="button"
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
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      className="flex-1 rounded-md border border-border px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted cursor-pointer"
                    >
                      Message
                    </button>
                  </div>
                </AnimatedCard>
              </Link>
            );
          })
        )}
      </motion.div>
    </div>
  );
}
