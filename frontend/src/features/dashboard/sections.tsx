import { useQuery } from "@tanstack/react-query";
import { Card, SectionHeader, Avatar } from "@/components/shared/primitives";
import {
  Plus,
  Flame,
  Users2,
  MessageSquare,
  ChevronRight,
  Calendar,
  Clock,
  Rocket,
  Sparkles,
  BrainCircuit,
  ArrowRight,
} from "lucide-react";
import { recommendationsApi } from "@/api";
import { messagesService, projectsService } from "@/services";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { TypoCaption, TypoCard, TypoBody, TypoSection } from "@/components/shared/Typography";

// 1. Current Projects
export function CurrentProjects() {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["dashboardCurrentProjects"],
    queryFn: () => projectsService.list(),
  });

  const fallbackProjects = [
    {
      id: "p1",
      name: "DevLink Platform",
      status: "in-progress" as const,
      progress: 80,
      completionPercentage: 80,
      deadlineText: "Due in 5 days",
      members: 4,
      maxMembers: 5,
      stars: 42,
      forks: 12,
      icon: "⚡",
      description: "Developer collaboration platform & showcase hub.",
      stack: ["React", "FastAPI", "TailwindCSS"],
      owner: "Alex",
      views: 120,
      avatars: [
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Alex",
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Sarah",
      ],
      extraAvatars: 3,
    },
    {
      id: "p2",
      name: "AI Matching Engine",
      status: "in-progress" as const,
      progress: 60,
      completionPercentage: 60,
      deadlineText: "Due in 12 days",
      members: 3,
      maxMembers: 4,
      stars: 28,
      forks: 7,
      icon: "🤖",
      description: "Match scoring engine for developers and teams.",
      stack: ["Python", "PyTorch", "Redis"],
      owner: "Priya",
      views: 85,
      avatars: [
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Priya",
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=John",
      ],
      extraAvatars: 2,
    },
    {
      id: "p3",
      name: "Mobile Collaboration App",
      status: "recruiting" as const,
      progress: 25,
      completionPercentage: 25,
      deadlineText: "Due in 18 days",
      members: 2,
      maxMembers: 5,
      stars: 15,
      forks: 3,
      icon: "📱",
      description: "Cross-platform mobile client for DevLink messages.",
      stack: ["React Native", "TypeScript", "Expo"],
      owner: "David",
      views: 54,
      avatars: ["https://api.dicebear.com/9.x/notionists-neutral/svg?seed=David"],
      extraAvatars: 1,
    },
  ];

  const displayProjects: any[] = projects.length > 0 ? projects.slice(0, 3) : fallbackProjects;

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Current Projects" action="View All" actionTo="/projects" />
      <div className="flex-1 px-4 sm:px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-border/40 space-y-2 animate-pulse bg-muted/20"
              >
                <div className="h-4 w-1/3 bg-muted rounded" />
                <div className="h-2 w-full bg-muted rounded-full" />
              </div>
            ))
          : displayProjects.map((p) => {
              const progressVal = p.progress ?? 0;
              const statusMap: Record<string, string> = {
                recruiting: "bg-primary/10 text-primary border-primary/20",
                "in-progress": "bg-warning/10 text-warning border-warning/30",
                completed: "bg-success/10 text-success border-success/30",
                archived: "bg-muted text-muted-foreground border-border",
              };
              const statusBadge = statusMap[p.status] || statusMap["in-progress"];
              const avatars = p.avatars || [];
              const extraAvatars = p.extraAvatars || 0;

              return (
                <div
                  key={p.id}
                  className="group relative flex flex-col gap-2.5 p-3.5 rounded-xl border border-border/50 hover:border-primary/40 bg-surface/50 hover:bg-muted/20 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary text-base font-bold border border-primary/20">
                        {p.icon || "🚀"}
                      </span>
                      <div className="min-w-0">
                        <Link
                          to="/projects/$projectId"
                          params={{ projectId: p.id }}
                          className="hover:text-primary transition-colors block truncate"
                        >
                          <TypoCard as="span" className="text-xs sm:text-sm font-bold text-foreground hover:text-primary truncate block">
                            {p.name}
                          </TypoCard>
                        </Link>
                        <TypoCaption as="p" className="text-[11px] text-muted-foreground truncate mt-0.5">
                          {p.description}
                        </TypoCaption>
                      </div>
                    </div>

                    <TypoCaption
                      as="span"
                      className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border shrink-0",
                        statusBadge,
                      )}
                    >
                      {(p.status || "Active").replace("-", " ")}
                    </TypoCaption>
                  </div>

                  {/* Progress bar + Completion percentage */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <TypoCaption as="span" className="text-muted-foreground font-medium">Completion</TypoCaption>
                      <TypoCaption as="span" className="font-bold text-foreground">{progressVal}%</TypoCaption>
                    </div>
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-300"
                        style={{ width: `${progressVal}%` }}
                      />
                    </div>
                  </div>

                  {/* Actionable info row: Team size & Deadline & Avatars */}
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/40 animate-fade-in">
                    <TypoCaption as="span" className="inline-flex items-center gap-1 font-medium text-foreground">
                      <Users2 size={12} className="text-primary" /> {p.members || 1} builders
                    </TypoCaption>

                    {/* Avatar stack */}
                    <div className="flex -space-x-1.5 items-center shrink-0">
                      {avatars.map((av: string, idx: number) => (
                        <Avatar
                          key={idx}
                          src={av}
                          alt="Team"
                          size={24}
                          className="border border-card ring-1 ring-border/20"
                        />
                      ))}
                      {extraAvatars > 0 && (
                        <div className="flex items-center justify-center h-6 w-6 rounded-full bg-muted border border-card text-[9px] font-semibold text-muted-foreground ring-1 ring-border/20">
                          +{extraAvatars}
                        </div>
                      )}
                    </div>

                    <TypoCaption as="span" className="inline-flex items-center gap-1 text-muted-foreground">
                      <Calendar size={12} />{" "}
                      {p.deadlineText || "Due in 10 days"}
                    </TypoCaption>
                  </div>
                </div>
              );
            })}
      </div>
    </Card>
  );
}

// 2. AI Suggestions / Recommendation Panel (#738)
export function AISuggestions() {
  const { data: recData, isLoading } = useQuery({
    queryKey: ["dashboardAIRecommendations"],
    queryFn: () => recommendationsApi.builders({ limit: 3 }),
  });

  const fallbackRecommendations = [
    {
      user_id: "b1",
      first_name: "Rahul",
      last_name: "Verma",
      username: "rahulv",
      role: "Backend Architect",
      headline: "Specializes in FastAPI, Distributed Systems & PostgreSQL",
      profile_image: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Rahul",
      score: 0.94,
      matched_skills: ["FastAPI", "Python", "PostgreSQL"],
      missing_skills: ["GraphQL", "Docker"],
      suggested_action: "Invite to Team",
    },
    {
      user_id: "b2",
      first_name: "Elena",
      last_name: "Rostova",
      username: "elenar",
      role: "AI / ML Engineer",
      headline: "Building LLM agents & RAG pipelines with PyTorch",
      profile_image: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Elena",
      score: 0.88,
      matched_skills: ["Python", "PyTorch", "LangChain"],
      missing_skills: ["Kubernetes"],
      suggested_action: "Connect",
    },
    {
      user_id: "b3",
      first_name: "Sarah",
      last_name: "Jenkins",
      username: "sarahj",
      role: "Fullstack Developer",
      headline: "React 19 & Tailwind CSS enthusiast with 4y exp",
      profile_image: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Sarah",
      score: 0.82,
      matched_skills: ["React", "TypeScript"],
      missing_skills: ["Next.js", "Redis"],
      suggested_action: "View Profile",
    },
  ];

  const results =
    recData?.results && recData.results.length > 0
      ? (recData.results as Array<Record<string, unknown>>).map((b, idx) => ({
          user_id: String(b.user_id || `b-${idx}`),
          first_name: String(b.first_name || "Developer"),
          last_name: String(b.last_name || ""),
          username: String(b.username || "builder"),
          role: String(b.role || "Software Engineer"),
          headline: String(b.headline || "Active open-source contributor"),
          profile_image:
            typeof b.profile_image === "string"
              ? b.profile_image
              : `https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${b.username || idx}`,
          score: typeof b.score === "number" ? b.score : 0.85,
          matched_skills: Array.isArray(b.matched_skills)
            ? (b.matched_skills as string[])
            : ["React", "TypeScript"],
          missing_skills: Array.isArray(b.missing_skills)
            ? (b.missing_skills as string[])
            : ["Redis"],
          suggested_action: idx === 0 ? "Invite to Team" : "Connect",
        }))
      : fallbackRecommendations;

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="AI Recommendations" action="View Matches" actionTo="/builders" />
      <div className="flex-1 px-4 sm:px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="p-3.5 rounded-xl border border-border/40 space-y-2 animate-pulse bg-muted/20"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-muted" />
                <div className="space-y-1 flex-1">
                  <div className="h-3 w-1/3 bg-muted rounded" />
                  <div className="h-2 w-1/2 bg-muted rounded" />
                </div>
              </div>
            </div>
          ))
        ) : results.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-6 text-center text-xs text-muted-foreground">
            <BrainCircuit size={28} className="text-primary/60 mb-2" />
            <TypoCard as="p" className="font-semibold text-foreground">No recommendations available</TypoCard>
            <TypoCaption as="p" className="mt-0.5">
              Add skills to your profile to get personalized AI collaborator matches.
            </TypoCaption>
          </div>
        ) : (
          results.map((rec) => {
            const matchPercentage = Math.round(rec.score * 100);
            const matchBadgeClass =
              matchPercentage >= 90
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                : matchPercentage >= 80
                  ? "bg-primary/15 text-primary border-primary/20"
                  : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/20";

            return (
              <div
                key={rec.user_id}
                className="group p-3.5 rounded-xl border border-border/50 hover:border-primary/40 bg-surface/50 hover:bg-muted/20 transition-all flex flex-col gap-2.5"
              >
                {/* Builder Row: Avatar, Name, Role, Match % */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <Avatar
                      src={rec.profile_image}
                      alt={`${rec.first_name} ${rec.last_name}`}
                      size={36}
                      className="border border-border/40 shrink-0"
                    />
                    <div className="min-w-0">
                      <Link
                        to="/profile/$username"
                        params={{ username: rec.username }}
                        className="hover:text-primary transition-colors block truncate"
                      >
                        <TypoCard as="span" className="text-xs sm:text-sm font-bold text-foreground hover:text-primary truncate block">
                          {rec.first_name} {rec.last_name}
                        </TypoCard>
                      </Link>
                      <TypoCaption as="p" className="text-[11px] text-muted-foreground truncate mt-0.5">{rec.role}</TypoCaption>
                    </div>
                  </div>

                  {/* Match Percentage Badge */}
                  <TypoCaption
                    as="span"
                    className={cn(
                      "text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 flex items-center gap-1",
                      matchBadgeClass,
                    )}
                  >
                    <Sparkles size={11} /> {matchPercentage}% Match
                  </TypoCaption>
                </div>

                {/* Skills Insights: Matched vs Missing */}
                <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                  {rec.matched_skills.slice(0, 2).map((sk: string) => (
                    <TypoCaption
                      as="span"
                      key={sk}
                      className="text-[10px] px-1.5 py-0.5 rounded-md bg-primary/10 text-primary font-medium border border-primary/20"
                    >
                      ✓ {sk}
                    </TypoCaption>
                  ))}
                  {rec.missing_skills.slice(0, 2).map((sk: string) => (
                    <TypoCaption
                      as="span"
                      key={sk}
                      className="text-[10px] px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground font-medium border border-border/60"
                    >
                      + {sk} needed
                    </TypoCaption>
                  ))}
                </div>

                {/* Actionable button footer */}
                <div className="flex items-center justify-between pt-2 border-t border-border/40 text-[11px]">
                  <TypoCaption as="span" className="text-muted-foreground truncate max-w-[180px]">
                    {rec.headline}
                  </TypoCaption>
                  <Link
                    to="/builders"
                    className="inline-flex items-center gap-1 font-semibold text-primary hover:underline shrink-0 cursor-pointer"
                  >
                    <TypoCaption as="span" className="text-primary font-semibold hover:underline">
                      {rec.suggested_action}
                    </TypoCaption>{" "}
                    <ArrowRight size={11} className="text-primary" />
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}

// 3. Quick Actions
export function QuickActions() {
  const actions = [
    {
      label: "Create Project",
      icon: Plus,
      bg: "bg-blue-50/50 dark:bg-blue-950/20",
      border: "border-blue-100 dark:border-blue-900/40",
      color: "text-blue-600 dark:text-blue-400",
      to: "/projects" as const,
    },
    {
      label: "Publish Flare",
      icon: Flame,
      bg: "bg-orange-50/50 dark:bg-orange-950/20",
      border: "border-orange-100 dark:border-orange-900/40",
      color: "text-orange-600 dark:text-orange-400",
      to: "/flares" as const,
    },
    {
      label: "Find Builders",
      icon: Users2,
      bg: "bg-emerald-50/50 dark:bg-emerald-950/20",
      border: "border-emerald-100 dark:border-emerald-900/40",
      color: "text-emerald-600 dark:text-emerald-400",
      to: "/builders" as const,
    },
    {
      label: "Messages",
      icon: MessageSquare,
      bg: "bg-purple-50/50 dark:bg-purple-950/20",
      border: "border-purple-100 dark:border-purple-900/40",
      color: "text-purple-600 dark:text-purple-400",
      to: "/messages" as const,
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <TypoSection as="h3" className="px-5 pt-5 pb-2 font-semibold text-sm text-foreground">
        Quick Actions
      </TypoSection>
      <div className="grid grid-cols-2 gap-3 p-4 pt-1 flex-1">
        {actions.map((act) => {
          const Icon = act.icon;
          return (
            <Link
              key={act.label}
              to={act.to}
              className={cn(
                "flex flex-col items-center justify-center gap-3 p-4 rounded-xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xs active:translate-y-0 text-center cursor-pointer",
                act.bg,
                act.border,
              )}
            >
              <div
                className={cn(
                  "flex items-center justify-center h-10 w-10 rounded-xl bg-card shadow-2xs border border-border/20",
                  act.color,
                )}
              >
                <Icon size={20} />
              </div>
              <TypoCard as="span" className="text-xs font-bold text-foreground">
                {act.label}
              </TypoCard>
            </Link>
          );
        })}
      </div>
    </Card>
  );
}

// 4. Recent Activity
export function RecentActivity() {
  const activities = [
    {
      id: "a1",
      bulletColor: "bg-blue-500",
      text: "Alex commented on DevLink Platform",
      time: "2 hours ago",
    },
    {
      id: "a2",
      bulletColor: "bg-emerald-500",
      text: "Sarah accepted your invitation",
      time: "Yesterday",
    },
    {
      id: "a3",
      bulletColor: "bg-purple-500",
      text: "New builder joined your team",
      time: "2 days ago",
    },
    {
      id: "a4",
      bulletColor: "bg-orange-500",
      text: "You published a new flare",
      time: "3 days ago",
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Recent Activity" action="View All" actionTo="/dashboard" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-3">
        {activities.map((act) => (
          <Link
            key={act.id}
            to="/dashboard"
            className="flex items-center justify-between gap-4 p-2.5 rounded-lg border border-transparent hover:border-border/40 hover:bg-muted/10 transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className={cn("h-2 w-2 rounded-full shrink-0", act.bulletColor)} />
              <div className="min-w-0">
                <TypoBody as="p" className="text-xs font-semibold text-foreground truncate">
                  {act.text}
                </TypoBody>
                <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-0.5">
                  {act.time}
                </TypoCaption>
              </div>
            </div>
            <ChevronRight size={14} className="text-muted-foreground shrink-0" />
          </Link>
        ))}
      </div>
    </Card>
  );
}

// 5. Upcoming (Center list widget)
export function Upcoming() {
  const upcomingList = [
    {
      id: "u1",
      title: "Web3 Hackathon",
      time: "Tomorrow, 10:00 AM",
      icon: Calendar,
      iconColor: "text-rose-500 bg-rose-500/10",
    },
    {
      id: "u2",
      title: "React Meetup",
      time: "Fri, 4:00 PM",
      icon: Calendar,
      iconColor: "text-blue-500 bg-blue-500/10",
    },
    {
      id: "u3",
      title: "Project Deadline",
      time: "May 20, 2025",
      icon: Clock,
      iconColor: "text-emerald-500 bg-emerald-500/10",
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Upcoming" action="View All" actionTo="/dashboard" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-3">
        {upcomingList.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className="flex items-center gap-3 p-2.5 rounded-lg border border-border/40"
            >
              <div
                className={cn(
                  "flex items-center justify-center h-8 w-8 rounded-lg shrink-0",
                  item.iconColor,
                )}
              >
                <Icon size={16} />
              </div>
              <div className="min-w-0">
                <TypoCard as="p" className="text-xs font-bold text-foreground truncate">
                  {item.title}
                </TypoCard>
                <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-0.5">
                  {item.time}
                </TypoCaption>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// 6. Compact Messaging Widget (Sidebar Widget - #741)
export function CompactMessagingWidget() {
  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ["compactMessagingWidget"],
    queryFn: () => messagesService.conversations(),
  });

  const fallbackConversations = [
    {
      id: "c1",
      with: {
        name: "Sarah Chen",
        avatar: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Sarah",
        online: true,
      },
      preview: "Sounds great! Let's sync tomorrow.",
      unread: 2,
      ago: "5m",
      isTyping: true,
    },
    {
      id: "c2",
      with: {
        name: "Alex Rivera",
        avatar: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Alex",
        online: true,
      },
      preview: "Merged the latest PR for auth.",
      unread: 0,
      ago: "25m",
      isTyping: false,
    },
    {
      id: "c3",
      with: {
        name: "David Kim",
        avatar: "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=David",
        online: false,
      },
      preview: "Can you review the wireframes?",
      unread: 1,
      ago: "2h",
      isTyping: false,
    },
  ];

  const displayConversations =
    conversations.length > 0
      ? conversations.slice(0, 3).map((c, idx) => ({
          ...c,
          isTyping: idx === 0,
        }))
      : fallbackConversations;

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col">
      <SectionHeader title="Messages" action="Open Chat" actionTo="/messages" />
      <div className="px-3.5 pb-4 pt-1 flex flex-col gap-1.5">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-2.5 p-2 rounded-xl border border-transparent animate-pulse"
            >
              <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
              <div className="space-y-1.5 flex-1">
                <div className="h-3 w-1/3 bg-muted rounded" />
                <div className="h-2 w-2/3 bg-muted rounded" />
              </div>
            </div>
          ))
        ) : displayConversations.length === 0 ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            <MessageSquare size={20} className="mx-auto mb-1 opacity-50" />
            <TypoCaption as="p">No active conversations</TypoCaption>
          </div>
        ) : (
          displayConversations.map((c) => (
            <Link
              key={c.id}
              to="/messages/$conversationId"
              params={{ conversationId: c.id }}
              className="group flex items-center gap-2.5 p-2 rounded-xl hover:bg-muted/40 transition-colors border border-transparent hover:border-border/40"
            >
              {/* Compact 32px Avatar with live online dot */}
              <div className="relative shrink-0">
                <Avatar
                  src={c.with.avatar}
                  alt={c.with.name}
                  size={32}
                  className="rounded-full border border-border/30"
                />
                {c.with.online && (
                  <span
                    className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-card"
                    title="Online"
                  />
                )}
              </div>

              {/* Message text and sender name */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1">
                  <TypoCard as="p" className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                    {c.with.name}
                  </TypoCard>
                  <TypoCaption as="span" className="text-[10px] text-muted-foreground shrink-0">{c.ago}</TypoCaption>
                </div>

                <div className="flex items-center justify-between gap-2 mt-0.5">
                  {c.isTyping ? (
                    <div className="flex items-center text-primary text-[11px] font-medium">
                      <TypingIndicator
                        className="p-0 text-primary scale-90 origin-left"
                        label="typing..."
                      />
                    </div>
                  ) : (
                    <TypoCaption as="p" className="text-[11px] text-muted-foreground truncate group-hover:text-foreground/80 transition-colors">
                      {c.preview}
                    </TypoCaption>
                  )}

                  {/* Unread badge */}
                  {c.unread > 0 && (
                    <TypoCaption as="span" className="grid place-items-center h-4 min-w-[16px] px-1 rounded-full bg-primary text-[9px] font-bold text-primary-foreground shrink-0">
                      {c.unread}
                    </TypoCaption>
                  )}
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}

// Notifications (Sidebar Widget)
export function NotificationsWidget() {
  const notifications = [
    {
      id: "n1",
      dotColor: "bg-blue-500",
      text: "Alex commented on your flare",
      time: "2 hours ago",
    },
    {
      id: "n2",
      dotColor: "bg-emerald-500",
      text: "Sarah accepted your invitation",
      time: "5 hours ago",
    },
    {
      id: "n3",
      dotColor: "bg-purple-500",
      text: "New builder joined DevLink",
      time: "1 day ago",
    },
    {
      id: "n4",
      dotColor: "bg-orange-500",
      text: "Your project is 80% complete",
      time: "2 days ago",
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col">
      <SectionHeader title="Notifications" action="View All" actionTo="/dashboard" />
      <div className="px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {notifications.map((n) => (
          <div key={n.id} className="flex items-start gap-3 min-w-0">
            <div className={cn("h-2.5 w-2.5 rounded-full shrink-0 mt-1", n.dotColor)} />
            <div className="min-w-0">
              <TypoBody as="p" className="text-xs font-semibold text-foreground leading-tight">{n.text}</TypoBody>
              <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-0.5">{n.time}</TypoCaption>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// 7. Upcoming Events (Sidebar Widget)
export function UpcomingEventsWidget() {
  const events = [
    {
      id: "e1",
      title: "Web3 Hackathon",
      time: "Tomorrow, 10:00 AM",
      iconColor: "text-rose-500 bg-rose-500/10",
    },
    {
      id: "e2",
      title: "React Meetup",
      time: "Fri, 4:00 PM",
      iconColor: "text-blue-500 bg-blue-500/10",
    },
    {
      id: "e3",
      title: "AI Builders Summit",
      time: "May 24, 9:00 AM",
      iconColor: "text-violet-500 bg-violet-500/10",
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col">
      <SectionHeader title="Upcoming Events" action="View All" actionTo="/dashboard" />
      <div className="px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {events.map((e) => (
          <div key={e.id} className="flex items-center gap-3">
            <div
              className={cn(
                "flex items-center justify-center h-8 w-8 rounded-lg shrink-0",
                e.iconColor,
              )}
            >
              <Calendar size={16} />
            </div>
            <div className="min-w-0">
              <TypoCard as="p" className="text-xs font-bold text-foreground truncate">{e.title}</TypoCard>
              <TypoCaption as="p" className="text-[11px] text-muted-foreground mt-0.5">{e.time}</TypoCaption>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// 8. Upgrade Plan CTA Card (Sidebar Card)
export function UpgradePlanCTA() {
  return (
    <Card className="border-border/60 rounded-2xl bg-blue-50/50 dark:bg-blue-950/10 shadow-xs p-5 relative overflow-hidden flex items-center gap-4">
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,183,215,0.04),transparent_60%)] pointer-events-none" />

      <div className="flex items-center justify-center h-12 w-12 rounded-xl shrink-0 bg-primary/10 text-primary relative z-10">
        <Rocket size={24} className="animate-bounce" />
      </div>

      <div className="min-w-0 flex-1 relative z-10">
        <TypoCard as="h4" className="text-sm font-bold text-foreground">Upgrade your plan</TypoCard>
        <TypoCaption as="p" className="text-xs text-muted-foreground mt-0.5">Unlock premium features and boost your productivity.</TypoCaption>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline mt-2 cursor-pointer"
        >
          <TypoCaption as="span" className="text-[11px] font-bold text-primary hover:underline">
            Upgrade Now
          </TypoCaption>{" "}
          <ChevronRight size={12} className="text-primary" />
        </Link>
      </div>
    </Card>
  );
}
