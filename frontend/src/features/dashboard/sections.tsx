import { ActivityFeed } from "@/components/activity/ActivityFeed";
import { Card, SectionHeader, TagChip, Avatar } from "@/components/shared/primitives";
import { useQuery } from "@tanstack/react-query";
import {
  activitiesService,
  dashboardService,
  buildersService,
  projectsService,
  flaresService,
  messagesService,
  notificationsService,
} from "@/services";
import {
  Check,
  X,
  Star,
  MessageCircle,
  FolderPlus,
  Flame,
  Users2,
  FileText,
  BarChart3,
  Trophy,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { motion, useReducedMotion } from "framer-motion";
import { containerVariants, cardEntrance, cardHover } from "@/lib/animations";

export function RecentActivity() {
  return (
    <Card>
      <ActivityFeed
        queryKey={["activities", "recent"]}
        queryFn={() => activitiesService.list(20)}
      />
    </Card>
  );
}

export function BuilderRequests() {
  const { data = [] } = useQuery({
    queryKey: ["builder-requests"],
    queryFn: dashboardService.builderRequests,
  });
  return (
    <Card>
      <SectionHeader title="Builder Requests" action="View All" />
      <ul className="divide-y divide-border/60">
        {data.map((r) => (
          <li key={r.id} className="px-4 py-3.5 transition-colors hover:bg-muted/30">
            <div className="flex items-start gap-3">
              <Avatar src={r.builder.avatar} alt={r.builder.name} size={42} />
              <div className="min-w-0 flex-1">
                <p className="text-[13px] font-bold text-foreground">{r.builder.name}</p>
                <p className="text-[12px] font-medium text-muted-foreground">{r.builder.role}</p>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {r.builder.skills.slice(0, 3).map((s) => (
                    <TagChip key={s}>{s}</TagChip>
                  ))}
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {r.builder.yearsExp} yrs exp ·{" "}
                  <span className="font-bold text-emerald-500">{r.builder.matchScore}% Match</span>
                </p>
              </div>
            </div>
            <div className="mt-2.5 flex gap-2">
              <button className="flex-1 rounded-xl bg-primary px-2.5 py-1.5 text-[12px] font-bold text-primary-foreground shadow-xs transition-opacity hover:opacity-90 active:scale-95">
                Accept
              </button>
              <button className="flex-1 rounded-xl border border-border/80 bg-surface px-2.5 py-1.5 text-[12px] font-semibold text-foreground transition-colors hover:bg-muted active:scale-95">
                Reject
              </button>
              <button className="rounded-xl border border-border/80 bg-surface px-2.5 py-1.5 text-[12px] font-semibold text-foreground transition-colors hover:bg-muted active:scale-95">
                View
              </button>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function InviteRequests() {
  const { data = [] } = useQuery({
    queryKey: ["invite-requests"],
    queryFn: dashboardService.inviteRequests,
  });
  return (
    <Card>
      <SectionHeader title="Invite Requests" action="View All" />
      <ul className="divide-y divide-border/60">
        {data.map((r) => (
          <li
            key={r.id}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30"
          >
            <span
              className={cn(
                "grid h-10 w-10 shrink-0 place-items-center rounded-xl text-lg shadow-xs",
                r.color,
              )}
            >
              {r.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-bold text-foreground">{r.project}</p>
              <p className="text-[11px] font-medium text-muted-foreground">{r.role}</p>
              <p className="text-[11px] text-muted-foreground">
                Due in {r.dueDays} days · By {r.by}
              </p>
            </div>
            <div className="flex gap-1.5">
              <button className="grid h-8 w-8 place-items-center rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-500 transition-colors hover:bg-emerald-500/20 active:scale-95">
                <Check size={15} />
              </button>
              <button className="grid h-8 w-8 place-items-center rounded-xl border border-destructive/30 bg-destructive/10 text-destructive transition-colors hover:bg-destructive/20 active:scale-95">
                <X size={15} />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
export function SuggestedBuilders() {
  const { data = [] } = useQuery({ queryKey: ["suggested"], queryFn: buildersService.suggested });
  const prefersReducedMotion = useReducedMotion();

  return (
    <Card>
      <SectionHeader title="Suggested Builders" action="View All" actionTo="/builders" />
      <motion.div
        className="grid grid-cols-1 gap-3.5 p-4 pt-0 sm:grid-cols-3"
        variants={containerVariants}
        initial={prefersReducedMotion ? undefined : "hidden"}
        animate={prefersReducedMotion ? undefined : "visible"}
      >
        {data.map((b, i) => (
          <motion.div
            key={b.id}
            variants={prefersReducedMotion ? undefined : cardEntrance}
            custom={i}
            whileHover={prefersReducedMotion ? undefined : cardHover}
            transition={{ duration: 0.2 }}
            className="will-change-transform flex flex-col items-center rounded-2xl border border-border/70 bg-card p-4 text-center shadow-xs transition-all hover:border-primary/40 hover:shadow-card"
          >
            <Avatar src={b.avatar} alt={b.name} size={60} online={b.online} />
            <p className="mt-3 text-[14px] font-bold text-foreground leading-tight">{b.name}</p>
            <p className="text-[11px] font-semibold text-muted-foreground leading-tight">
              {b.role}
            </p>
            <p className="text-[11px] text-muted-foreground">{b.country}</p>
            <div className="mt-2.5 flex flex-wrap justify-center gap-1.5">
              {b.skills.slice(0, 2).map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
            <p className="mt-2 text-[11px] font-semibold text-muted-foreground">
              {b.yearsExp} yrs exp
            </p>
            <p className="text-[11px] font-bold text-emerald-500">{b.matchScore}% Match</p>
            <div className="mt-3 flex w-full gap-1.5">
              <button className="flex-1 rounded-xl bg-primary px-2 py-1.5 text-[11px] font-bold text-primary-foreground shadow-xs transition-opacity hover:opacity-90 active:scale-95">
                Connect
              </button>
              <button className="flex-1 rounded-xl border border-border/80 px-2 py-1.5 text-[11px] font-semibold text-foreground transition-colors hover:bg-muted active:scale-95">
                Message
              </button>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </Card>
  );
}


export function TrendingProjects() {
  const { data = [] } = useQuery({ queryKey: ["trending"], queryFn: projectsService.trending });
  return (
    <Card>
      <SectionHeader title="Trending Projects" action="View All" actionTo="/projects" />
      <ul className="divide-y divide-border/60">
        {data.map((p) => (
          <li
            key={p.id}
            className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-muted/30"
          >
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-muted text-lg shadow-xs">
              {p.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-bold text-foreground">{p.name}</p>
              <p className="truncate text-[11px] font-medium text-muted-foreground">
                {p.stack.join(" · ")}
              </p>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-semibold text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Star size={13} className="text-amber-500 fill-amber-500" /> {p.stars}
              </span>
              <span className="inline-flex items-center gap-1">
                <MessageCircle size={13} /> {p.forks}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function AIRecommendations() {
  return (
    <Card className="relative overflow-hidden">
      <SectionHeader title="AI Recommendations" action="View All" />
      <div className="space-y-3 px-5 pb-5">
        <p className="text-[13px] font-medium text-foreground leading-relaxed">
          You need a <span className="font-bold text-foreground">Backend Developer</span> for your
          project <span className="font-bold text-primary">AI Chatbot</span>
        </p>
        <div className="rounded-2xl border border-primary/30 bg-primary-soft/30 p-3.5 shadow-xs">
          <p className="text-[10px] font-bold uppercase tracking-wider text-primary">Top Match</p>
          <div className="mt-2 flex items-center gap-3">
            <Avatar
              src="https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Rahul"
              alt="Rahul"
              size={42}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-bold text-foreground">Rahul Verma</p>
              <p className="text-[11px] font-medium text-muted-foreground">Full Stack Developer</p>
              <p className="text-[11px] font-bold text-emerald-500">93% Match</p>
            </div>
            <button className="rounded-xl bg-primary px-3 py-1.5 text-[12px] font-bold text-primary-foreground shadow-xs transition-opacity hover:opacity-90 active:scale-95">
              Invite
            </button>
          </div>
        </div>
        <div className="rounded-2xl bg-muted/60 p-3.5">
          <p className="text-[11px] font-bold text-foreground">Why this match?</p>
          <ul className="mt-2 space-y-1.5 text-[11px] font-medium text-muted-foreground">
            <li className="flex items-center gap-1.5">
              <Check size={13} className="text-emerald-500" /> Skills match 90%
            </li>
            <li className="flex items-center gap-1.5">
              <Check size={13} className="text-emerald-500" /> Past experience
            </li>
            <li className="flex items-center gap-1.5">
              <Check size={13} className="text-emerald-500" /> Available this week
            </li>
          </ul>
          <button className="mt-2.5 text-[11px] font-bold text-primary transition-all hover:text-primary/80 hover:underline">
            Learn More →
          </button>
        </div>
      </div>
    </Card>
  );
}

export function MessagesPreview() {
  const { data = [] } = useQuery({
    queryKey: ["conversations"],
    queryFn: messagesService.conversations,
  });
  return (
    <Card>
      <SectionHeader title="Messages Preview" action="View All" actionTo="/messages" />
      <ul className="divide-y divide-border/60">
        {data.map((c) => (
          <li key={c.id}>
            <Link
              to="/messages/$conversationId"
              params={{ conversationId: c.id }}
              className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-muted/40"
            >
              <Avatar src={c.with.avatar} alt={c.with.name} size={34} online={c.with.online} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-bold text-foreground">{c.with.name}</p>
                <p className="truncate text-[12px] font-medium text-muted-foreground">
                  {c.preview}
                </p>
              </div>
              <span className="text-[11px] font-medium text-muted-foreground">{c.ago}</span>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function QuickActions() {
  const actions = [
    {
      icon: FolderPlus,
      label: "New Project",
      tint: "bg-blue-500/10 text-blue-500",
      to: "/projects" as const,
    },
    {
      icon: Flame,
      label: "Create Flare",
      tint: "bg-amber-500/10 text-amber-500",
      to: "/flares" as const,
    },
    {
      icon: Users2,
      label: "Find Builder",
      tint: "bg-emerald-500/10 text-emerald-500",
      to: "/builders" as const,
    },
    {
      icon: Trophy,
      label: "Start Hackathon",
      tint: "bg-cyan-500/10 text-cyan-500",
      to: "/hackathons" as const,
    },
    {
      icon: FileText,
      label: "AI Description",
      tint: "bg-rose-500/10 text-rose-500",
      to: "/dashboard" as const,
    },
    {
      icon: BarChart3,
      label: "View Analytics",
      tint: "bg-blue-500/10 text-blue-500",
      to: "/analytics" as const,
    },
  ];
  return (
    <Card>
      <SectionHeader title="Quick Actions" />
      <div className="grid grid-cols-3 gap-3 p-4 pt-0">
        {actions.map((a) => (
          <Link
            key={a.label}
            to={a.to}
            className="group flex flex-col items-center gap-2.5 rounded-2xl border border-border/70 bg-card p-3 text-center transition-all duration-200 hover:border-primary/40 hover:shadow-card hover:-translate-y-0.5"
          >
            <span
              className={cn(
                "grid h-11 w-11 place-items-center rounded-xl transition-transform duration-200 group-hover:scale-105",
                a.tint,
              )}
            >
              <a.icon size={18} />
            </span>
            <span className="text-[11px] font-bold text-foreground leading-tight">{a.label}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

export function UpcomingDeadlines() {
  const { data = [] } = useQuery({ queryKey: ["deadlines"], queryFn: dashboardService.deadlines });
  const sevTint = {
    danger: "text-destructive font-bold",
    warning: "text-amber-500 font-bold",
    info: "text-blue-500 font-bold",
  } as const;
  return (
    <Card>
      <SectionHeader title="Upcoming Deadlines" action="View Calendar" />
      <ul className="divide-y divide-border/60">
        {data.map((d) => (
          <li
            key={d.id}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
          >
            <FolderPlus size={15} className="shrink-0 text-muted-foreground" />
            <p className="min-w-0 flex-1 truncate text-[13px] font-medium text-foreground">
              {d.project} — <span className="text-muted-foreground">{d.milestone}</span>
            </p>
            <span className={cn("whitespace-nowrap text-[11px]", sevTint[d.severity])}>
              Due in {d.dueDays} days
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function NotificationsFeed() {
  const { data = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsService.list,
  });
  return (
    <Card>
      <SectionHeader title="Notifications Feed" action="View All" actionTo="/notifications" />
      <ul className="divide-y divide-border/60">
        {data.map((n) => (
          <li
            key={n.id}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
          >
            <span
              className={cn(
                "h-2 w-2 shrink-0 rounded-full ring-2 ring-card",
                n.unread ? "bg-primary animate-pulse" : "bg-transparent",
              )}
            />
            <p className="min-w-0 flex-1 truncate text-[13px] font-medium text-foreground">
              {n.text}
            </p>
            <span className="text-[11px] font-medium text-muted-foreground">{n.ago}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
