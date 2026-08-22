import React from "react";
import {
  Rocket,
  Users,
  UserCheck,
  CheckCircle2,
  Archive,
  Clock,
  CircleDot,
  Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { TypoSection, TypoCaption, TypoCard } from "@/components/shared/Typography";

export type TimelineEventType =
  "project_created" | "recruitment_started" | "members_joined" | "milestone_completed" | "archived";

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: string;
  status?: "completed" | "in_progress" | "upcoming";
  actor?: {
    name: string;
    avatar?: string;
  };
}

export interface ProjectTimelineProps {
  events?: TimelineEvent[];
  className?: string;
  title?: string;
}

const defaultEvents: TimelineEvent[] = [
  {
    id: "1",
    type: "project_created",
    title: "Project Created",
    description: "Initial project repository and workspace initialized.",
    timestamp: "2026-01-15T10:00:00Z",
    status: "completed",
  },
  {
    id: "2",
    type: "recruitment_started",
    title: "Recruitment Started",
    description: "Open flares posted seeking Frontend and Backend collaborators.",
    timestamp: "2026-01-18T14:30:00Z",
    status: "completed",
  },
  {
    id: "3",
    type: "members_joined",
    title: "Members Joined",
    description: "3 core contributors joined the development team.",
    timestamp: "2026-01-22T09:15:00Z",
    status: "completed",
  },
  {
    id: "4",
    type: "milestone_completed",
    title: "Milestones Completed",
    description: "Beta release and MVP features successfully shipped.",
    timestamp: "2026-02-01T16:00:00Z",
    status: "in_progress",
  },
  {
    id: "5",
    type: "archived",
    title: "Archived",
    description: "Project lifecycle completion and long-term maintenance state.",
    timestamp: "2026-03-01T00:00:00Z",
    status: "upcoming",
  },
];

const eventConfig: Record<
  TimelineEventType,
  { icon: React.ComponentType<{ className?: string }>; color: string; bgColor: string }
> = {
  project_created: {
    icon: Rocket,
    color: "text-blue-500 dark:text-blue-400",
    bgColor: "bg-blue-500/10 border-blue-500/20",
  },
  recruitment_started: {
    icon: Users,
    color: "text-amber-500 dark:text-amber-400",
    bgColor: "bg-amber-500/10 border-amber-500/20",
  },
  members_joined: {
    icon: UserCheck,
    color: "text-purple-500 dark:text-purple-400",
    bgColor: "bg-purple-500/10 border-purple-500/20",
  },
  milestone_completed: {
    icon: CheckCircle2,
    color: "text-emerald-500 dark:text-emerald-400",
    bgColor: "bg-emerald-500/10 border-emerald-500/20",
  },
  archived: {
    icon: Archive,
    color: "text-slate-500 dark:text-slate-400",
    bgColor: "bg-slate-500/10 border-slate-500/20",
  },
};

export function ProjectTimeline({
  events = defaultEvents,
  className,
  title = "Project Milestones & Activity Timeline",
}: ProjectTimelineProps) {
  return (
    <section
      aria-label={title}
      className={cn("rounded-xl border border-border bg-card p-6 shadow-sm", className)}
    >
      <div className="mb-6 flex items-center justify-between">
        <TypoSection>
          <Calendar className="h-4 w-4 text-primary" aria-hidden="true" />
          {title}
        </TypoSection>
        <TypoCaption>
          {events.filter((e) => e.status === "completed").length} of {events.length} completed
        </TypoCaption>
      </div>

      <ol className="relative ml-3 border-l border-border/80 space-y-6" role="list">
        {events.map((event, index) => {
          const config = eventConfig[event.type] || {
            icon: CircleDot,
            color: "text-muted-foreground",
            bgColor: "bg-muted",
          };
          const Icon = config.icon;
          const isLast = index === events.length - 1;

          return (
            <li key={event.id} className="relative pl-6 group">
              {/* Icon badge dot on timeline */}
              <span
                className={cn(
                  "absolute -left-3 top-0.5 flex h-6 w-6 items-center justify-center rounded-full border bg-background transition-transform group-hover:scale-110",
                  event.status === "completed"
                    ? config.bgColor
                    : event.status === "in_progress"
                      ? "border-primary bg-primary/10 text-primary animate-pulse"
                      : "border-border bg-muted text-muted-foreground",
                )}
                aria-hidden="true"
              >
                <Icon className={cn("h-3.5 w-3.5", config.color)} />
              </span>

              {/* Event Content Card */}
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1">
                <TypoCard>
                  {event.title}
                  {event.status === "completed" && (
                    <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                      Completed
                    </span>
                  )}
                  {event.status === "in_progress" && (
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                      In Progress
                    </span>
                  )}
                  {event.status === "upcoming" && <TypoCaption>Upcoming</TypoCaption>}
                </TypoCard>
                <time
                  dateTime={event.timestamp}
                  className="text-xs text-muted-foreground flex items-center gap-1 shrink-0"
                >
                  <Clock className="h-3 w-3" />
                  {new Date(event.timestamp).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </time>
              </div>

              {event.description && <TypoCaption as="p">{event.description}</TypoCaption>}

              {event.actor && (
                <div className="mt-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <span className="font-medium text-foreground">{event.actor.name}</span>
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
