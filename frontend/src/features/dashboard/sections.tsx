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
import { useQuery } from "@tanstack/react-query";
import {
  projectsService,
  buildersService,
  activitiesService,
  hackathonsService,
  notificationsService,
} from "@/services";

// 1. Current Projects
export function CurrentProjects() {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["dashboard-projects"],
    queryFn: () => projectsService.list({ limit: 3 }),
  });

  const projectsList = projects.slice(0, 3).map((p) => ({
    id: p.id,
    name: p.name,
    status: p.status
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" "),
    progress: p.progress,
    dueText: "Active", // Not part of the API model
    iconText: p.icon || p.name.charAt(0),
    iconBg: "bg-blue-500/10 text-blue-500 border border-blue-500/20",
    avatars: [
      `https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${p.name}1`,
      `https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${p.name}2`,
    ],
    extraAvatars: Math.max(0, p.members - 2),
  }));

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Current Projects" action="View All" actionTo="/projects" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-16 rounded-xl border border-border/40 bg-muted/50 animate-pulse"
            />
          ))
        ) : projectsList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
            <p className="text-sm">No projects found</p>
          </div>
        ) : (
          projectsList.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between gap-4 p-3 rounded-xl border border-border/40 hover:bg-muted/10 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={cn(
                    "flex items-center justify-center h-10 w-10 shrink-0 rounded-lg text-sm font-bold",
                    p.iconBg,
                  )}
                >
                  {p.iconText}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground truncate">{p.name}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{p.status}</p>
                </div>
              </div>

              {/* Progress bar stack */}
              <div className="flex items-center gap-4 shrink-0">
                <div className="hidden sm:flex flex-col items-end gap-1">
                  <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${p.progress}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-muted-foreground">
                    {p.progress}%
                  </span>
                </div>

                {/* Avatar stack */}
                <div className="flex -space-x-1.5 items-center shrink-0">
                  {p.avatars.map((av, idx) => (
                    <Avatar
                      key={idx}
                      src={av}
                      alt="Team"
                      size={24}
                      className="border border-card ring-1 ring-border/20"
                    />
                  ))}
                  {p.extraAvatars > 0 && (
                    <div className="flex items-center justify-center h-6 w-6 rounded-full bg-muted border border-card text-[9px] font-semibold text-muted-foreground ring-1 ring-border/20">
                      +{p.extraAvatars}
                    </div>
                  )}
                </div>

                <span className="text-xs font-medium text-muted-foreground whitespace-nowrap hidden md:inline">
                  {p.dueText}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

// 2. AI Suggestions
export function AISuggestions() {
  const { data: builders = [], isLoading } = useQuery({
    queryKey: ["dashboard-ai-suggestions"],
    queryFn: () => buildersService.suggested(),
  });

  const suggestions = builders.slice(0, 3).map((b, i) => {
    // Generate some diverse suggestion badges for demo purposes
    const isTop = i === 0;
    const isEvent = i === 1;
    return {
      id: b.id,
      icon: isEvent ? Calendar : isTop ? User : TrendingUp,
      iconColor: isEvent
        ? "text-blue-500 bg-blue-500/10"
        : isTop
          ? "text-emerald-500 bg-emerald-500/10"
          : "text-amber-500 bg-amber-500/10",
      text: isEvent
        ? `${b.name} invited you to an event`
        : isTop
          ? `${b.name} matches your backend role`
          : `${b.name} liked your profile`,
      badge: isEvent ? "Event" : isTop ? `${b.matchScore || 95}% Match` : "Connect",
      badgeClass: isEvent
        ? "bg-blue-500/15 text-blue-500 border border-blue-500/20"
        : isTop
          ? "bg-success/15 text-success border border-success/20"
          : "bg-amber-500/15 text-amber-500 border border-amber-500/20",
    };
  });

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="AI Suggestions" action="View All" actionTo="/builders" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-12 rounded-xl border border-border/40 bg-muted/50 animate-pulse"
            />
          ))
        ) : suggestions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
            <p className="text-sm">No suggestions yet</p>
          </div>
        ) : (
          suggestions.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.id}
                className="flex items-center justify-between gap-4 p-3.5 rounded-xl border border-border/40 hover:bg-muted/10 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={cn(
                      "flex items-center justify-center h-8 w-8 rounded-lg shrink-0",
                      s.iconColor,
                    )}
                  >
                    <Icon size={16} />
                  </div>
                  <p className="text-xs font-semibold text-foreground truncate">{s.text}</p>
                </div>
                <span
                  className={cn(
                    "text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0",
                    s.badgeClass,
                  )}
                >
                  {s.badge}
                </span>
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
      <div className="px-5 pt-5 pb-2 font-semibold text-sm text-foreground">Quick Actions</div>
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
  const { data: activities = [], isLoading } = useQuery({
    queryKey: ["dashboard-activity"],
    queryFn: () => activitiesService.list(4),
  });

  const activityList = activities.slice(0, 4).map((a, i) => {
    const colors = ["bg-blue-500", "bg-emerald-500", "bg-purple-500", "bg-orange-500"];
    return {
      id: a.id,
      bulletColor: colors[i % colors.length],
      text: a.title || "Unknown activity",
      time: new Date(a.created_at).toLocaleDateString(),
    };
  });

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Recent Activity" action="View All" actionTo="/dashboard" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-3">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-10 rounded-lg border border-transparent bg-muted/30 animate-pulse"
            />
          ))
        ) : activityList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
            <p className="text-xs">No recent activity</p>
          </div>
        ) : (
          activityList.map((act) => (
            <Link
              key={act.id}
              to="/dashboard"
              className="flex items-center justify-between gap-4 p-2.5 rounded-lg border border-transparent hover:border-border/40 hover:bg-muted/10 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={cn("h-2 w-2 rounded-full shrink-0", act.bulletColor)} />
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate">{act.text}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{act.time}</p>
                </div>
              </div>
              <ChevronRight size={14} className="text-muted-foreground shrink-0" />
            </Link>
          ))
        )}
      </div>
    </Card>
  );
}

// 5. Upcoming (Center list widget)
export function Upcoming() {
  const { data: hackathons = [], isLoading } = useQuery({
    queryKey: ["dashboard-upcoming"],
    queryFn: () => hackathonsService.list(),
  });

  const upcomingList = hackathons.slice(0, 3).map((h, i) => {
    const colors = [
      "text-rose-500 bg-rose-500/10",
      "text-blue-500 bg-blue-500/10",
      "text-emerald-500 bg-emerald-500/10",
    ];
    return {
      id: h.id,
      title: h.name,
      time: new Date(h.starts_at).toLocaleDateString(),
      icon: Calendar,
      iconColor: colors[i % colors.length],
    };
  });

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col h-full">
      <SectionHeader title="Upcoming" action="View All" actionTo="/dashboard" />
      <div className="flex-1 px-5 pb-5 pt-1 flex flex-col gap-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-12 rounded-lg border border-border/40 bg-muted/30 animate-pulse"
            />
          ))
        ) : upcomingList.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground">
            <p className="text-xs">No upcoming events</p>
          </div>
        ) : (
          upcomingList.map((item) => {
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
                  <p className="text-xs font-bold text-foreground truncate">{item.title}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{item.time}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}

// 6. Notifications (Sidebar Widget)
export function NotificationsWidget() {
  const { data: rawNotifications = [], isLoading } = useQuery({
    queryKey: ["dashboard-notifications"],
    queryFn: () => notificationsService.list(),
  });

  const notifications = rawNotifications.slice(0, 4).map((n, i) => {
    const colors = ["bg-blue-500", "bg-emerald-500", "bg-purple-500", "bg-orange-500"];
    return {
      id: n.id || `n${i}`,
      dotColor: colors[i % colors.length],
      text: n.title,
      time: n.created_at ? new Date(n.created_at).toLocaleDateString() : "Recently",
    };
  });

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col">
      <SectionHeader title="Notifications" action="View All" actionTo="/dashboard" />
      <div className="px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-8 rounded-lg border border-transparent bg-muted/30 animate-pulse"
            />
          ))
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-4 text-center text-muted-foreground">
            <p className="text-xs">You have no notifications</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className="flex items-start gap-3 min-w-0">
              <div className={cn("h-2.5 w-2.5 rounded-full shrink-0 mt-1", n.dotColor)} />
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground leading-tight">{n.text}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{n.time}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

// 7. Upcoming Events (Sidebar Widget)
export function UpcomingEventsWidget() {
  const { data: hackathons = [], isLoading } = useQuery({
    queryKey: ["dashboard-upcoming-events"],
    queryFn: () => hackathonsService.list(),
  });

  const events = hackathons.slice(0, 3).map((h, i) => {
    const colors = [
      "text-rose-500 bg-rose-500/10",
      "text-blue-500 bg-blue-500/10",
      "text-violet-500 bg-violet-500/10",
    ];
    return {
      id: h.id,
      title: h.name,
      time: new Date(h.starts_at).toLocaleDateString(),
      iconColor: colors[i % colors.length],
    };
  });

  return (
    <Card className="border-border/60 rounded-2xl bg-card shadow-xs flex flex-col">
      <SectionHeader title="Upcoming Events" action="View All" actionTo="/dashboard" />
      <div className="px-5 pb-5 pt-1 flex flex-col gap-3.5">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-10 rounded-lg border border-transparent bg-muted/30 animate-pulse"
            />
          ))
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-4 text-center text-muted-foreground">
            <p className="text-xs">No upcoming events</p>
          </div>
        ) : (
          events.map((e) => (
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
                <p className="text-xs font-bold text-foreground truncate">{e.title}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{e.time}</p>
              </div>
            </div>
          ))
        )}
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
        <h4 className="text-sm font-bold text-foreground">Upgrade your plan</h4>
        <p className="text-[11px] text-muted-foreground mt-1 leading-normal">
          Unlock premium features and boost your productivity.
        </p>
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
