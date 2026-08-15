import React, { useState } from "react";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import { format, parse, startOfWeek, getDay } from "date-fns";
import { enUS } from "date-fns/locale/en-US";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api";
import { Card } from "@/components/shared/primitives";
import { TypoSection } from "@/components/shared/Typography";
import "react-big-calendar/lib/css/react-big-calendar.css";

const locales = {
  "en-US": enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

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

export const ProjectCalendar: React.FC<ProjectCalendarProps> = ({ projectId, currentUserRole }) => {
  const { data: events, isLoading } = useQuery<CalendarEvent[]>({
    queryKey: ["projectCalendarEvents", projectId],
    queryFn: () => api.get<CalendarEvent[]>(`/projects/${projectId}/calendar-events`),
  });

  const formattedEvents = (events || []).map((e) => ({
    title: e.title,
    start: new Date(e.start_date),
    end: e.end_date ? new Date(e.end_date) : new Date(e.start_date),
    resource: e,
  }));

  const getEventStyle = (event: any) => {
    let backgroundColor = "#3b82f6"; // blue default
    if (event.resource.event_type === "milestone") backgroundColor = "#10b981"; // green
    if (event.resource.event_type === "sprint") backgroundColor = "#8b5cf6"; // purple
    if (event.resource.event_type === "meeting") backgroundColor = "#f59e0b"; // amber
    if (event.resource.event_type === "hackathon") backgroundColor = "#ef4444"; // red

    return {
      style: {
        backgroundColor,
        borderRadius: "4px",
        opacity: 0.9,
        color: "white",
        border: "0px",
        display: "block",
      },
    };
  };

  if (isLoading) {
    return <div className="p-8 text-center animate-pulse text-muted-foreground">Loading calendar...</div>;
  }

  return (
    <Card className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <TypoSection>Project Calendar</TypoSection>
        <div className="flex items-center gap-3 text-xs font-semibold">
          <span className="flex items-center gap-1"><div className="h-3 w-3 rounded-full bg-emerald-500"></div> Milestone</span>
          <span className="flex items-center gap-1"><div className="h-3 w-3 rounded-full bg-purple-500"></div> Sprint</span>
          <span className="flex items-center gap-1"><div className="h-3 w-3 rounded-full bg-amber-500"></div> Meeting</span>
          <span className="flex items-center gap-1"><div className="h-3 w-3 rounded-full bg-red-500"></div> Hackathon</span>
          <span className="flex items-center gap-1"><div className="h-3 w-3 rounded-full bg-blue-500"></div> Other</span>
        </div>
      </div>
      <div style={{ height: "600px" }}>
        <Calendar
          localizer={localizer}
          events={formattedEvents}
          startAccessor="start"
          endAccessor="end"
          eventPropGetter={getEventStyle}
          views={["month", "week", "day"]}
          defaultView="month"
          className="text-sm font-sans"
        />
      </div>
    </Card>
  );
};
