import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { notificationsService } from "@/services";
import api from "@/lib/api";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import { useState, useMemo, useEffect } from "react";
import {
  Check,
  Trash2,
  Archive,
  Bell,
  MessageSquare,
  UserPlus,
  Zap,
  Trophy,
  Inbox,
  CheckCircle2,
  MoreHorizontal,
} from "lucide-react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import type { Notification } from "@/services";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({
    meta: [
      { title: "Notifications — DevLink" },
      { name: "description", content: "All your DevLink notifications in one place." },
    ],
  }),
  component: NotificationsPage,
});

type FilterType = "All" | "Unread" | "Mentions" | "Applications";

const ICON_MAP = {
  apply: UserPlus,
  comment: MessageSquare,
  invite: Inbox,
  match: Zap,
  hackathon: Trophy,
};

const COLOR_MAP = {
  apply: "text-blue-500 bg-blue-500/10 border-blue-500/20",
  comment: "text-purple-500 bg-purple-500/10 border-purple-500/20",
  invite: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  match: "text-green-500 bg-green-500/10 border-green-500/20",
  hackathon: "text-rose-500 bg-rose-500/10 border-rose-500/20",
};

// Helper to group by date
function getGroup(ago: string) {
  const lower = ago.toLowerCase();
  if (lower.includes("m ago") || lower.includes("h ago") || lower.includes("just now"))
    return "Today";
  if (lower.includes("1d ago")) return "Yesterday";
  return "Earlier";
}

function NotificationsPage() {
  const {
    data = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsService.list,
  });

  const [localNotifs, setLocalNotifs] = useState<Notification[]>([]);
  const [activeFilter, setActiveFilter] = useState<FilterType>("All");
  const [page, setPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    if (data.length > 0) {
      setLocalNotifs(data);
    }
  }, [data]);

  const handleMarkAllRead = async () => {
    setLocalNotifs((prev) => prev.map((n) => ({ ...n, unread: false })));
    try {
      await api.patch("/api/notifications/read-all");
    } catch {}
  };

  const handleMarkRead = async (id: string) => {
    setLocalNotifs((prev) => prev.map((n) => (n.id === id ? { ...n, unread: false } : n)));
    try {
      await api.patch(`/api/notifications/${id}/read`);
    } catch {}
  };

  const handleDelete = async (id: string) => {
    setLocalNotifs((prev) => prev.filter((n) => n.id !== id));
    try {
      await api.delete(`/api/notifications/${id}`);
    } catch {}
  };

  const handleArchive = async (id: string) => {
    setLocalNotifs((prev) => prev.filter((n) => n.id !== id));
    try {
      await api.delete(`/api/notifications/${id}`);
    } catch {}
  };

  const filtered = useMemo(() => {
    return localNotifs.filter((n) => {
      if (activeFilter === "Unread") return n.unread;
      if (activeFilter === "Mentions") return n.kind === "comment";
      if (activeFilter === "Applications") return n.kind === "apply" || n.kind === "invite";
      return true;
    });
  }, [localNotifs, activeFilter]);

  const paginated = useMemo(() => {
    return filtered.slice(0, page * itemsPerPage);
  }, [filtered, page]);

  const hasMore = paginated.length < filtered.length;

  const grouped = useMemo(() => {
    const groups: Record<string, Notification[]> = { Today: [], Yesterday: [], Earlier: [] };
    paginated.forEach((n) => {
      groups[getGroup(n.ago)].push(n);
    });
    return groups;
  }, [paginated]);

  const unreadCount = localNotifs.filter((n) => n.unread).length;

  if (error) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <EmptyState
          icon={Bell}
          title="Something went wrong"
          desc="We couldn't load your notifications. Please try again."
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <TypoHeading as="h1">
            Notifications
            {unreadCount > 0 && (
              <span className="flex h-6 items-center justify-center rounded-full bg-primary/10 px-2.5 text-xs font-semibold text-primary">
                {unreadCount} unread
              </span>
            )}
          </TypoHeading>
          <TypoCaption as="p">Catch up on what you've missed.</TypoCaption>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="flex items-center gap-2 rounded-md border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-muted disabled:opacity-50"
            aria-label="Mark all as read"
          >
            <CheckCircle2 className="h-4 w-4" />
            Mark all read
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-8 md:flex-row md:items-start">
        {/* Sidebar Filters */}
        <div className="w-full shrink-0 space-y-1 md:w-56">
          {(["All", "Unread", "Mentions", "Applications"] as FilterType[]).map((filter) => (
            <button
              key={filter}
              onClick={() => {
                setActiveFilter(filter);
                setPage(1);
              }}
              className={cn(
                "flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                activeFilter === filter
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {filter}
              {filter === "Unread" && unreadCount > 0 && (
                <span
                  className={cn(
                    "flex h-5 items-center justify-center rounded-full px-2 text-[10px]",
                    activeFilter === filter
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-primary/10 text-primary",
                  )}
                >
                  {unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notifications Feed */}
        <div className="flex-1 space-y-6">
          {isLoading ? (
            <Card className="divide-y divide-border overflow-hidden">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-start gap-4 p-4">
                  <Skeleton className="h-10 w-10 shrink-0 rounded-full" />
                  <div className="space-y-2 flex-1 pt-1">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              ))}
            </Card>
          ) : paginated.length === 0 ? (
            <Card className="py-12">
              <EmptyState
                icon={CheckCircle2}
                title="All caught up!"
                desc={
                  activeFilter === "All"
                    ? "You don't have any notifications right now."
                    : `No ${activeFilter.toLowerCase()} notifications.`
                }
              />
            </Card>
          ) : (
            <div className="space-y-8">
              {(["Today", "Yesterday", "Earlier"] as const).map((group) => {
                const items = grouped[group];
                if (items.length === 0) return null;

                return (
                  <div
                    key={group}
                    className="space-y-3 animate-in fade-in slide-in-from-bottom-4 duration-500"
                  >
                    <TypoSection>{group}</TypoSection>
                    <Card className="overflow-hidden">
                      <ul className="divide-y divide-border">
                        {items.map((n) => {
                          const Icon = ICON_MAP[n.kind as keyof typeof ICON_MAP] || Bell;
                          return (
                            <li
                              key={n.id}
                              className={cn(
                                "group relative flex items-start gap-4 p-4 transition-colors hover:bg-muted/50",
                                n.unread && "bg-primary/5",
                              )}
                            >
                              <div className="relative mt-1">
                                <div
                                  className={cn(
                                    "flex h-10 w-10 shrink-0 items-center justify-center rounded-full border shadow-sm",
                                    COLOR_MAP[n.kind as keyof typeof COLOR_MAP] ||
                                      "bg-muted text-muted-foreground border-border",
                                  )}
                                >
                                  <Icon className="h-5 w-5" />
                                </div>
                                {n.unread && (
                                  <span className="absolute -right-1 -top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-background">
                                    <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                                  </span>
                                )}
                              </div>

                              <div className="flex-1 min-w-0 pt-0.5">
                                <p
                                  className={cn(
                                    "text-sm leading-relaxed",
                                    n.unread
                                      ? "font-medium text-foreground"
                                      : "text-muted-foreground",
                                  )}
                                >
                                  {n.text}
                                </p>
                                <TypoCaption as="p">{n.ago}</TypoCaption>
                              </div>

                              <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                                {n.unread && (
                                  <button
                                    onClick={() => handleMarkRead(n.id)}
                                    className="rounded-md p-2 text-muted-foreground hover:bg-background hover:text-primary hover:shadow-xs transition-colors"
                                    title="Mark as read"
                                    aria-label="Mark as read"
                                  >
                                    <Check className="h-4 w-4" />
                                  </button>
                                )}
                                <DropdownMenu.Root>
                                  <DropdownMenu.Trigger asChild>
                                    <button
                                      className="rounded-md p-2 text-muted-foreground hover:bg-background hover:text-foreground hover:shadow-xs transition-colors"
                                      aria-label="More options"
                                    >
                                      <MoreHorizontal className="h-4 w-4" />
                                    </button>
                                  </DropdownMenu.Trigger>
                                  <DropdownMenu.Portal>
                                    <DropdownMenu.Content
                                      align="end"
                                      className="z-50 min-w-[160px] overflow-hidden rounded-xl border border-border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2"
                                    >
                                      <DropdownMenu.Item
                                        className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-muted hover:text-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                                        onClick={() => handleArchive(n.id)}
                                      >
                                        <Archive className="mr-2 h-4 w-4" />
                                        Archive
                                      </DropdownMenu.Item>
                                      <DropdownMenu.Item
                                        className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-destructive/10 hover:text-destructive data-[disabled]:pointer-events-none data-[disabled]:opacity-50 text-destructive"
                                        onClick={() => handleDelete(n.id)}
                                      >
                                        <Trash2 className="mr-2 h-4 w-4" />
                                        Delete
                                      </DropdownMenu.Item>
                                    </DropdownMenu.Content>
                                  </DropdownMenu.Portal>
                                </DropdownMenu.Root>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </Card>
                  </div>
                );
              })}

              {hasMore && (
                <div className="pt-4 pb-8 flex justify-center">
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded-full border border-border bg-card px-6 py-2 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-muted hover:shadow-md"
                  >
                    Load more
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
