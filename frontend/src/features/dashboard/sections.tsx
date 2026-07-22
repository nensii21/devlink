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
      <ul className="divide-y divide-border">
        {data.map((r) => (
          <li key={r.id} className="px-4 py-3">
            <div className="flex items-start gap-3">
              <Avatar src={r.builder.avatar} alt={r.builder.name} size={40} />
              <div className="min-w-0 flex-1">
                <p className="text-[13px] font-semibold text-foreground">{r.builder.name}</p>
                <p className="text-[12px] text-muted-foreground">{r.builder.role}</p>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {r.builder.skills.slice(0, 3).map((s) => (
                    <TagChip key={s}>{s}</TagChip>
                  ))}
                </div>
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  {r.builder.yearsExp} yrs exp ·{" "}
                  <span className="font-semibold text-success">{r.builder.matchScore}% Match</span>
                </p>
              </div>
            </div>
            <div className="mt-2 flex gap-1.5">
              <button className="flex-1 rounded-md bg-primary px-2 py-1 text-[12px] font-semibold text-primary-foreground hover:opacity-90">
                Accept
              </button>
              <button className="flex-1 rounded-md border border-border bg-surface px-2 py-1 text-[12px] font-medium text-foreground hover:bg-muted">
                Reject
              </button>
              <button className="rounded-md border border-border bg-surface px-2 py-1 text-[12px] font-medium text-foreground hover:bg-muted">
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
      <ul className="divide-y divide-border">
        {data.map((r) => (
          <li key={r.id} className="flex items-center gap-3 px-4 py-3">
            <span
              className={cn(
                "grid h-10 w-10 shrink-0 place-items-center rounded-md text-lg",
                r.color,
              )}
            >
              {r.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-foreground">{r.project}</p>
              <p className="text-[11px] text-muted-foreground">{r.role}</p>
              <p className="text-[11px] text-muted-foreground">
                Due in {r.dueDays} days · By {r.by}
              </p>
            </div>
            <div className="flex gap-1">
              <button className="grid h-7 w-7 place-items-center rounded-md border border-success/30 bg-success/10 text-success hover:bg-success/20">
                <Check size={14} />
              </button>
              <button className="grid h-7 w-7 place-items-center rounded-md border border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/20">
                <X size={14} />
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
        className="grid grid-cols-1 gap-3 p-4 pt-0 sm:grid-cols-3"
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
            className="will-change-transform rounded-md border border-border p-3 text-center"
          >
            <Avatar src={b.avatar} alt={b.name} size={56} online={b.online} />
            <p className="mt-2 text-[13px] font-semibold text-foreground">{b.name}</p>
            <p className="text-[11px] text-muted-foreground">{b.role}</p>
            <p className="text-[11px] text-muted-foreground">{b.country}</p>
            <div className="mt-1.5 flex flex-wrap justify-center gap-1">
              {b.skills.slice(0, 2).map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-muted-foreground">{b.yearsExp} yrs exp</p>
            <p className="text-[11px] font-semibold text-success">{b.matchScore}% Match</p>
            <div className="mt-2 flex gap-1.5">
              <button className="flex-1 rounded-md bg-primary px-2 py-1 text-[11px] font-semibold text-primary-foreground hover:opacity-90">
                Connect
              </button>
              <button className="flex-1 rounded-md border border-border px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted">
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
      <ul className="divide-y divide-border">
        {data.map((p) => (
          <li key={p.id} className="flex items-center gap-3 px-4 py-2.5">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-muted text-lg">
              {p.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
              <p className="truncate text-[11px] text-muted-foreground">{p.stack.join(" · ")}</p>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Star size={12} /> {p.stars}
              </span>
              <span className="inline-flex items-center gap-1">
                <MessageCircle size={12} /> {p.forks}
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
    <Card>
      <SectionHeader title="AI Recommendations" action="View All" />
      <div className="space-y-3 px-4 pb-4">
        <p className="text-[13px] text-foreground">
          You need a <span className="font-semibold">Backend Developer</span> for your project{" "}
          <span className="font-semibold text-primary">AI Chatbot</span>
        </p>
        <div className="rounded-md border border-border p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Top Match
          </p>
          <div className="mt-2 flex items-center gap-3">
            <Avatar
              src="https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Rahul"
              alt="Rahul"
              size={40}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-foreground">Rahul Verma</p>
              <p className="text-[11px] text-muted-foreground">Full Stack Developer</p>
              <p className="text-[11px] font-semibold text-success">93% Match</p>
            </div>
            <button className="rounded-md bg-primary px-2.5 py-1 text-[12px] font-semibold text-primary-foreground hover:opacity-90">
              Invite
            </button>
          </div>
        </div>
        <div className="rounded-md bg-muted/50 p-3">
          <p className="text-[11px] font-semibold text-foreground">Why this match?</p>
          <ul className="mt-1.5 space-y-1 text-[11px] text-muted-foreground">
            <li className="flex items-center gap-1.5">
              <Check size={12} className="text-success" /> Skills match 90%
            </li>
            <li className="flex items-center gap-1.5">
              <Check size={12} className="text-success" /> Past experience
            </li>
            <li className="flex items-center gap-1.5">
              <Check size={12} className="text-success" /> Available this week
            </li>
          </ul>
          <button className="mt-2 text-[11px] font-semibold text-primary hover:underline">
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
      <ul className="divide-y divide-border">
        {data.map((c) => (
          <li key={c.id}>
            <Link
              to="/messages/$conversationId"
              params={{ conversationId: c.id }}
              className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50"
            >
              <Avatar src={c.with.avatar} alt={c.with.name} size={32} online={c.with.online} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-semibold text-foreground">{c.with.name}</p>
                <p className="truncate text-[12px] text-muted-foreground">{c.preview}</p>
              </div>
              <span className="text-[11px] text-muted-foreground">{c.ago}</span>
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
      tint: "bg-info/10 text-info",
      to: "/projects" as const,
    },
    {
      icon: Flame,
      label: "Create Flare",
      tint: "bg-warning/10 text-warning",
      to: "/flares" as const,
    },
    {
      icon: Users2,
      label: "Find Builder",
      tint: "bg-success/10 text-success",
      to: "/builders" as const,
    },
    {
      icon: Trophy,
      label: "Start Hackathon",
      tint: "bg-primary-soft text-primary",
      to: "/hackathons" as const,
    },
    {
      icon: FileText,
      label: "AI Description",
      tint: "bg-destructive/10 text-destructive",
      to: "/dashboard" as const,
    },
    {
      icon: BarChart3,
      label: "View Analytics",
      tint: "bg-info/10 text-info",
      to: "/analytics" as const,
    },
  ];
  return (
    <Card>
      <SectionHeader title="Quick Actions" />
      <div className="grid grid-cols-3 gap-2 p-4 pt-0">
        {actions.map((a) => (
          <Link
            key={a.label}
            to={a.to}
            className="flex flex-col items-center gap-1.5 rounded-md border border-border p-2 text-center transition-colors hover:bg-muted"
          >
            <span className={cn("grid h-8 w-8 place-items-center rounded-md", a.tint)}>
              <a.icon size={14} />
            </span>
            <span className="text-[11px] font-medium text-foreground">{a.label}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

export function UpcomingDeadlines() {
  const { data = [] } = useQuery({ queryKey: ["deadlines"], queryFn: dashboardService.deadlines });
  const sevTint = {
    danger: "text-destructive",
    warning: "text-warning",
    info: "text-info",
  } as const;
  return (
    <Card>
      <SectionHeader title="Upcoming Deadlines" action="View Calendar" />
      <ul className="divide-y divide-border">
        {data.map((d) => (
          <li key={d.id} className="flex items-center gap-3 px-4 py-2.5">
            <FolderPlus size={14} className="shrink-0 text-muted-foreground" />
            <p className="min-w-0 flex-1 truncate text-[13px] text-foreground">
              {d.project} — <span className="text-muted-foreground">{d.milestone}</span>
            </p>
            <span
              className={cn("whitespace-nowrap text-[11px] font-semibold", sevTint[d.severity])}
            >
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
      <ul className="divide-y divide-border">
        {data.map((n) => (
          <li key={n.id} className="flex items-center gap-3 px-4 py-2.5">
            <span
              className={cn(
                "h-2 w-2 shrink-0 rounded-full",
                n.unread ? "bg-primary" : "bg-transparent",
              )}
            />
            <p className="min-w-0 flex-1 truncate text-[13px] text-foreground">{n.text}</p>
            <span className="text-[11px] text-muted-foreground">{n.ago}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
