import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Announcement {
  id: string;
  title: string;
  content: string;
  severity: "info" | "warning" | "critical";
  target_audience: "all" | "developers" | "admins";
  start_date: string;
  end_date?: string;
  is_active: boolean;
}

const DISMISSED_STORAGE_KEY = "devlink_dismissed_announcements";

export function AnnouncementBanner() {
  const [dismissedIds, setDismissedIds] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(DISMISSED_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // An empty list is a valid answer meaning "nothing to announce", and a
  // failure means we do not know. Both render nothing.
  //
  // This used to substitute a hardcoded "Scheduled Maintenance tonight from
  // 2:00 AM to 3:00 AM UTC" for either case -- dated `new Date()`, so it was
  // always tonight, on every page, for every user, forever. It was also the
  // `useQuery` default, so it rendered during the first load before any
  // request resolved (#1249).
  //
  // A fake maintenance notice is the piece of invented content users are most
  // likely to act on.
  const { data: announcements = [] } = useQuery<Announcement[]>({
    queryKey: ["global-announcements-active"],
    queryFn: async (): Promise<Announcement[]> => {
      const res = await api.get<Announcement[]>("/api/announcements/active");
      return res ?? [];
    },
    refetchInterval: 60000,
    // The banner is decoration on top of whatever page the user is on. A
    // failure should cost them nothing, so it stays quiet and retries on the
    // interval above rather than surfacing an error over their content.
    retry: 1,
  });

  const activeAnnouncements = announcements.filter((item) => !dismissedIds.includes(item.id));

  const handleDismiss = (id: string) => {
    const updated = [...dismissedIds, id];
    setDismissedIds(updated);
    try {
      localStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // ignore storage errors
    }
  };

  if (activeAnnouncements.length === 0) return null;

  return (
    <div className="w-full space-y-1 z-40">
      {activeAnnouncements.map((ann) => {
        const isCritical = ann.severity === "critical";
        const isWarning = ann.severity === "warning";

        return (
          <div
            key={ann.id}
            className={cn(
              "flex items-center justify-between px-4 py-2.5 text-xs sm:text-sm font-medium transition-all shadow-sm",
              isCritical
                ? "bg-destructive text-destructive-foreground"
                : isWarning
                  ? "bg-amber-500 text-white dark:bg-amber-600"
                  : "bg-primary text-primary-foreground",
            )}
          >
            <div className="flex items-center gap-2.5 flex-1 min-w-0 pr-2">
              {isCritical ? (
                <AlertCircle className="h-4 w-4 shrink-0" />
              ) : isWarning ? (
                <AlertTriangle className="h-4 w-4 shrink-0" />
              ) : (
                <Info className="h-4 w-4 shrink-0" />
              )}
              <div className="truncate">
                <span className="font-bold mr-1.5">{ann.title}:</span>
                <span>{ann.content}</span>
              </div>
            </div>
            <button
              onClick={() => handleDismiss(ann.id)}
              className="p-1 rounded-md hover:bg-black/10 transition-colors shrink-0"
              aria-label="Dismiss banner"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
