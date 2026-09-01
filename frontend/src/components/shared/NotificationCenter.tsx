import React, { useState, useEffect, useMemo } from "react";
import {
  Bell,
  Check,
  CheckCircle,
  FolderPlus,
  MessageCircle,
  MessageSquare,
  Users,
  XCircle,
  AtSign,
  Trash2,
} from "lucide-react";
import { formatDistanceToNow, isToday, isYesterday } from "date-fns";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

type NotificationType = string;

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
  avatar?: string;
}

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case "project_invite":
      return <FolderPlus className="h-4 w-4 text-blue-500" />;
    case "team_request":
    case "role_change":
      return <Users className="h-4 w-4 text-indigo-500" />;
    case "comment":
      return <MessageCircle className="h-4 w-4 text-green-500" />;
    case "mention":
      return <AtSign className="h-4 w-4 text-purple-500" />;
    case "application_accepted":
    case "application":
      return <CheckCircle className="h-4 w-4 text-emerald-500" />;
    case "application_rejected":
      return <XCircle className="h-4 w-4 text-red-500" />;
    case "message":
      return <MessageSquare className="h-4 w-4 text-sky-500" />;
    default:
      return <Bell className="h-4 w-4 text-gray-500" />;
  }
};

function getGroupHeader(createdAtStr: string): "Today" | "Yesterday" | "Earlier" {
  try {
    const d = new Date(createdAtStr);
    if (isToday(d)) return "Today";
    if (isYesterday(d)) return "Yesterday";
  } catch {
    // fallback
  }
  return "Earlier";
}

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState<"all" | "unread" | "mentions" | "applications">("all");
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      return api.get<Notification[]>("/api/notifications/");
    },
    enabled: !!user,
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAllMutation = useMutation({
    mutationFn: async () => {
      await api.patch("/api/notifications/read-all");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/api/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/notifications/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllAsRead = () => {
    markAllMutation.mutate();
  };

  const markAsRead = (id: string) => {
    markReadMutation.mutate(id);
  };

  const deleteNotification = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteMutation.mutate(id);
  };

  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }, 15000);
    return () => clearInterval(interval);
  }, [user, queryClient]);

  const filteredNotifications = useMemo(() => {
    return notifications.filter((n) => {
      if (filter === "unread") return !n.is_read;
      if (filter === "mentions") return n.type === "mention";
      if (filter === "applications") {
        return (
          n.type === "application" ||
          n.type === "application_accepted" ||
          n.type === "application_rejected" ||
          n.type === "project_invite"
        );
      }
      return true;
    });
  }, [notifications, filter]);

  const groupedNotifications = useMemo(() => {
    const groups: Record<"Today" | "Yesterday" | "Earlier", Notification[]> = {
      Today: [],
      Yesterday: [],
      Earlier: [],
    };
    filteredNotifications.forEach((n) => {
      groups[getGroupHeader(n.created_at)].push(n);
    });
    return groups;
  }, [filteredNotifications]);

  const NotificationItem = ({ notification }: { notification: Notification }) => (
    <div
      className={cn(
        "flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer group relative",
        !notification.is_read && "bg-muted/30",
      )}
      onClick={() => {
        if (!notification.is_read) {
          markAsRead(notification.id);
        }
      }}
    >
      <div className="mt-1 shrink-0 rounded-full bg-background p-1.5 shadow-xs border border-border">
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 space-y-1 overflow-hidden pr-6">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium leading-none text-foreground truncate">
            {notification.title}
          </p>
          <TypoCaption>
            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
          </TypoCaption>
        </div>
        <TypoCaption as="p">{notification.message}</TypoCaption>
      </div>

      <div className="shrink-0 flex items-center gap-1.5">
        {!notification.is_read && <div className="h-2 w-2 rounded-full bg-primary" />}
        <button
          onClick={(e) => deleteNotification(e, notification.id)}
          className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-all"
          title="Delete notification"
          aria-label="Delete notification"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          className="relative grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground outline-hidden focus-visible:ring-2 focus-visible:ring-primary/20"
          aria-label="Notifications"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-[16px] place-items-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground animate-in zoom-in">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[380px] p-0 sm:w-[420px] rounded-xl shadow-xl overflow-hidden"
        align="end"
        sideOffset={8}
      >
        <Tabs value={filter} onValueChange={(val) => setFilter(val as any)} className="w-full">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface">
            <TypoHeading as="h2">Notifications</TypoHeading>
            <div className="flex items-center gap-2">
              <TabsList className="h-8">
                <TabsTrigger value="all" className="text-xs px-2.5">
                  All
                </TabsTrigger>
                <TabsTrigger value="unread" className="text-xs px-2.5">
                  Unread
                  {unreadCount > 0 && (
                    <span className="ml-1 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                      {unreadCount}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="mentions" className="text-xs px-2.5">
                  Mentions
                </TabsTrigger>
                <TabsTrigger value="applications" className="text-xs px-2.5">
                  Apps
                </TabsTrigger>
              </TabsList>
            </div>
          </div>

          <div className="flex items-center justify-between px-4 py-2 border-b border-border/50 bg-muted/20">
            <TypoCaption>You have {unreadCount} unread notifications</TypoCaption>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
                onClick={markAllAsRead}
                disabled={markAllMutation.isPending}
              >
                <Check className="mr-1.5 h-3 w-3" />
                Mark all read
              </Button>
            )}
          </div>

          <ScrollArea className="h-[400px]">
            <TabsContent value={filter} className="m-0 focus-visible:outline-hidden focus-visible:ring-0">
              {filteredNotifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <Bell className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-sm">No notifications found</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-border/50">
                  {(["Today", "Yesterday", "Earlier"] as const).map((group) => {
                    const items = groupedNotifications[group];
                    if (items.length === 0) return null;
                    return (
                      <div key={group}>
                        <div className="px-4 py-1.5 bg-muted/40 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                          {group}
                        </div>
                        {items.map((notification) => (
                          <NotificationItem key={notification.id} notification={notification} />
                        ))}
                      </div>
                    );
                  })}
                </div>
              )}
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </PopoverContent>
    </Popover>
  );
}
