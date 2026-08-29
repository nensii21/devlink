import React, { useState } from "react";
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
} from "date-fns";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api";
import { Card } from "@/components/shared/primitives";
import { TypoSection } from "@/components/shared/Typography";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock } from "lucide-react";

interface CalendarEvent {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  event_type: string;
  start_date: string;
  end_date: string | null;
}

interface ProjectCalendarProps {
  projectId: string;
  currentUserRole: string;
}

const eventTypeStyles: Record<string, { bg: string; text?: string; dot: string; label: string }> = {
  milestone: {
    bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400",
    dot: "bg-emerald-500",
    label: "Milestone",
  },
  sprint: {
    bg: "bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400",
    dot: "bg-purple-500",
    label: "Sprint",
  },
  meeting: {
    bg: "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400",
    dot: "bg-amber-500",
    label: "Meeting",
  },
  hackathon: {
    bg: "bg-red-500/10 border-red-500/30 text-red-600 dark:text-red-400",
    dot: "bg-red-500",
    label: "Hackathon",
  },
  default: {
    bg: "bg-primary/10 border-primary/30 text-primary",
    dot: "bg-primary",
    label: "Other",
  },
};

export const ProjectCalendar: React.FC<ProjectCalendarProps> = ({ projectId }) => {
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const { data: events = [], isLoading } = useQuery<CalendarEvent[]>({
    queryKey: ["projectCalendarEvents", projectId],
    queryFn: () => api.get<CalendarEvent[]>(`/projects/${projectId}/calendar-events`),
  });

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart);
  const endDate = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  const getDayEvents = (day: Date) => {
    return events.filter((e) => isSameDay(new Date(e.start_date), day));
  };

  const selectedDateEvents = events.filter((e) => isSameDay(new Date(e.start_date), selectedDate));

  if (isLoading) {
    return (
      <Card className="p-8 text-center animate-pulse text-muted-foreground">
        Loading calendar...
      </Card>
    );
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <TypoSection>Project Calendar</TypoSection>
          <p className="text-xs text-muted-foreground mt-0.5">
            Key milestones, sprints, meetings, and deadlines
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-medium">
          {Object.entries(eventTypeStyles)
            .filter(([key]) => key !== "default")
            .map(([key, style]) => (
              <span key={key} className="flex items-center gap-1.5 text-muted-foreground">
                <div className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
                {style.label}
              </span>
            ))}
        </div>
      </div>

      {/* Calendar Navigation */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarIcon size={18} className="text-primary" />
          <h3 className="text-base font-semibold text-foreground">
            {format(currentMonth, "MMMM yyyy")}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
          >
            <ChevronLeft size={16} />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 text-xs font-semibold"
            onClick={() => {
              const now = new Date();
              setCurrentMonth(now);
              setSelectedDate(now);
            }}
          >
            Today
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
          >
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>

      {/* Calendar Grid & Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Month View Grid */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-4">
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-muted-foreground mb-2">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div key={day} className="py-1">
                {day}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {days.map((day) => {
              const dayEvents = getDayEvents(day);
              const isSelected = isSameDay(day, selectedDate);
              const isCurrentMonthDay = isSameMonth(day, currentMonth);
              const isToday = isSameDay(day, new Date());

              return (
                <button
                  key={day.toISOString()}
                  type="button"
                  onClick={() => setSelectedDate(day)}
                  className={`min-h-[64px] p-1.5 rounded-lg border text-left flex flex-col justify-between transition-colors ${
                    isSelected
                      ? "border-primary bg-primary/5 ring-1 ring-primary"
                      : isToday
                        ? "border-primary/50 bg-muted/40"
                        : "border-border/60 hover:bg-muted/30"
                  } ${!isCurrentMonthDay ? "opacity-40" : ""}`}
                >
                  <span
                    className={`text-xs font-semibold inline-block rounded-full px-1.5 py-0.5 ${
                      isToday
                        ? "bg-primary text-primary-foreground"
                        : isSelected
                          ? "text-primary font-bold"
                          : "text-foreground"
                    }`}
                  >
                    {format(day, "d")}
                  </span>

                  {dayEvents.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {dayEvents.slice(0, 3).map((event) => {
                        const style = eventTypeStyles[event.event_type] || eventTypeStyles.default;
                        return (
                          <div
                            key={event.id}
                            title={event.title}
                            className={`h-1.5 w-1.5 rounded-full ${style.dot}`}
                          />
                        );
                      })}
                      {dayEvents.length > 3 && (
                        <span className="text-[9px] text-muted-foreground">
                          +{dayEvents.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Day Agenda */}
        <div className="rounded-xl border border-border bg-card p-4 flex flex-col">
          <div className="flex items-center justify-between border-b border-border pb-3 mb-3">
            <h4 className="text-sm font-semibold text-foreground">
              {format(selectedDate, "EEEE, MMMM d")}
            </h4>
            <span className="text-xs text-muted-foreground">
              {selectedDateEvents.length} event{selectedDateEvents.length !== 1 ? "s" : ""}
            </span>
          </div>

          {selectedDateEvents.length === 0 ? (
            <div className="py-12 text-center text-xs text-muted-foreground flex-1 flex flex-col items-center justify-center">
              <CalendarIcon size={24} className="mb-2 opacity-30" />
              No events scheduled for this day
            </div>
          ) : (
            <div className="space-y-2.5 overflow-y-auto max-h-[350px]">
              {selectedDateEvents.map((event) => {
                const style = eventTypeStyles[event.event_type] || eventTypeStyles.default;
                return (
                  <div
                    key={event.id}
                    className={`p-3 rounded-lg border text-xs flex flex-col gap-1 ${style.bg}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm">{event.title}</span>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-background/50">
                        {event.event_type}
                      </span>
                    </div>
                    {event.description && <p className="text-xs opacity-90">{event.description}</p>}
                    <div className="flex items-center gap-1 text-[11px] opacity-75 mt-1">
                      <Clock size={12} />
                      <span>{format(new Date(event.start_date), "p")}</span>
                      {event.end_date && <span> - {format(new Date(event.end_date), "p")}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
