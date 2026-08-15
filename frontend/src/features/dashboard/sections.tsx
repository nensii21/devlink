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
  User,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { TypoCaption, TypoCard } from "@/components/shared/Typography";

// 1. Current Projects
export function CurrentProjects() {
  const projectsList = [
    {
      id: "p1",
      name: "DevLink Platform",
      status: "In Progress",
      progress: 80,
      dueText: "Due in 5 days",
      iconText: "D",
      iconBg: "bg-blue-500/10 text-blue-500 border border-blue-500/20",
      avatars: [
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Alex",
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Sarah",
      ],
      extraAvatars: 3,
    },
    {
      id: "p2",
      name: "AI Matching Engine",
      status: "In Progress",
      progress: 60,
      dueText: "Due in 12 days",
      iconText: "A",
      iconBg: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20",
      avatars: [
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=Priya",
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=John",
      ],
      extraAvatars: 2,
    },
    {
      id: "p3",
      name: "Mobile App",
      status: "Planning",
      progress: 25,
      dueText: "Due in 18 days",
      iconText: "M",
      iconBg: "bg-violet-500/10 text-violet-500 border border-violet-500/20",
      avatars: [
        "https://api.dicebear.com/9.x/notionists-neutral/svg?seed=David",
      ],
      extraAvatars: 1,
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Current Projects" action="View All" actionTo="/projects" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-4">
        {projectsList.map((p) => (
          <div key={p.id} className="flex items-center justify-between gap-4 p-3 rounded-xl border border-border/40 hover:bg-muted/10 transition-colors">
            <div className="flex items-center gap-3 min-w-0">
              <div className={cn("flex items-center justify-center h-10 w-10 shrink-0 rounded-lg text-sm font-bold", p.iconBg)}>
                {p.iconText}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">{p.name}</p>
                <TypoCaption as="p">{p.status}</TypoCaption>
              </div>
            </div>

            {/* Progress bar stack */}
            <div className="flex items-center gap-4 shrink-0">
              <div className="hidden sm:flex flex-col items-end gap-1">
                <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${p.progress}%` }} />
                </div>
                <TypoCaption>{p.progress}%</TypoCaption>
              </div>

              {/* Avatar stack */}
              <div className="flex -space-x-1.5 items-center shrink-0">
                {p.avatars.map((av, idx) => (
                  <Avatar key={idx} src={av} alt="Team" size={24} className="border border-card ring-1 ring-border/20" />
                ))}
                {p.extraAvatars > 0 && (
                  <div className="flex items-center justify-center h-6 w-6 rounded-full bg-muted border border-card text-[9px] font-semibold text-muted-foreground ring-1 ring-border/20">
                    +{p.extraAvatars}
                  </div>
                )}
              </div>

              <TypoCaption>
                {p.dueText}
              </TypoCaption>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// 2. AI Suggestions
export function AISuggestions() {
  const suggestions = [
    {
      id: "s1",
      icon: User,
      iconColor: "text-emerald-500 bg-emerald-500/10",
      text: "Rahul Verma matches your backend role",
      badge: "94% Match",
      badgeClass: "bg-success/15 text-success border border-success/20",
    },
    {
      id: "s2",
      icon: Calendar,
      iconColor: "text-blue-500 bg-blue-500/10",
      text: "React Meetup in your city this Friday",
      badge: "Event",
      badgeClass: "bg-blue-500/15 text-blue-500 border border-blue-500/20",
    },
    {
      id: "s3",
      icon: TrendingUp,
      iconColor: "text-amber-500 bg-amber-500/10",
      text: "Your profile is 85% complete",
      badge: "Improve",
      badgeClass: "bg-amber-500/15 text-amber-500 border border-amber-500/20",
    },
  ];

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="AI Suggestions" action="View All" actionTo="/builders" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-4">
        {suggestions.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.id} className="flex items-center justify-between gap-4 p-3.5 rounded-xl border border-border/40 hover:bg-muted/10 transition-colors">
              <div className="flex items-center gap-3 min-w-0">
                <div className={cn("flex items-center justify-center h-8 w-8 rounded-lg shrink-0", s.iconColor)}>
                  <Icon size={16} />
                </div>
                <p className="text-xs font-semibold text-foreground truncate">{s.text}</p>
              </div>
              <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0", s.badgeClass)}>
                {s.badge}
              </span>
            </div>
          );
        })}
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
      <div className="px-5 pt-5 pb-2 font-semibold text-sm text-foreground">
        Quick Actions
      </div>
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
                act.border
              )}
            >
              <div className={cn("flex items-center justify-center h-10 w-10 rounded-xl bg-card shadow-2xs border border-border/20", act.color)}>
                <Icon size={20} />
              </div>
              <span className="text-xs font-bold text-foreground">{act.label}</span>
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
                <p className="text-xs font-semibold text-foreground truncate">{act.text}</p>
                <TypoCaption as="p">{act.time}</TypoCaption>
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
            <div key={item.id} className="flex items-center gap-3 p-2.5 rounded-lg border border-border/40">
              <div className={cn("flex items-center justify-center h-8 w-8 rounded-lg shrink-0", item.iconColor)}>
                <Icon size={16} />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-foreground truncate">{item.title}</p>
                <TypoCaption as="p">{item.time}</TypoCaption>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// 6. Notifications (Sidebar Widget)
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
              <p className="text-xs font-semibold text-foreground leading-tight">{n.text}</p>
              <TypoCaption as="p">{n.time}</TypoCaption>
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
            <div className={cn("flex items-center justify-center h-8 w-8 rounded-lg shrink-0", e.iconColor)}>
              <Calendar size={16} />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-foreground truncate">{e.title}</p>
              <TypoCaption as="p">{e.time}</TypoCaption>
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
        <TypoCard>Upgrade your plan</TypoCard>
        <TypoCaption as="p">
          Unlock premium features and boost your productivity.
        </TypoCaption>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline mt-2 cursor-pointer"
        >
          Upgrade Now <ChevronRight size={12} />
        </Link>
      </div>
    </Card>
  );
}
