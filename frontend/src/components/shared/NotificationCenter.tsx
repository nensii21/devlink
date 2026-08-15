import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

// Update the type based on backend
type NotificationType = string;

interface Notification {
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
      return <Users className="h-4 w-4 text-indigo-500" />;
    case "comment":
      return <MessageCircle className="h-4 w-4 text-green-500" />;
    case "mention":
      return <AtSign className="h-4 w-4 text-purple-500" />;
    case "application_accepted":
      return <CheckCircle className="h-4 w-4 text-emerald-500" />;
    case "application_rejected":
      return <XCircle className="h-4 w-4 text-red-500" />;
    case "message":
      return <MessageSquare className="h-4 w-4 text-sky-500" />;
    default:
      return <Bell className="h-4 w-4 text-gray-500" />;
  }
};

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    // api.get resolves to the parsed body directly; there is no `.data`
    // envelope to unwrap, and unwrapping one left the panel permanently empty.
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

  const markAllAsRead = () => {
    markAllMutation.mutate();
  };

  const markAsRead = (id: string) => {
    markReadMutation.mutate(id);
  };

  // Basic WebSocket Integration
  useEffect(() => {
    if (!user) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const token = localStorage.getItem("token") || "";
    // Connect to collab ws as that handles personal messages too? Actually there's websocket_collab and websocket_chat.
    // For now we'll just periodically refetch or use simple polling if ws is not fully configured for notifications globally.
    // Assuming backend emits to /ws/chat?token= or similar.
    // We'll rely on react-query polling or simple invalidation.
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }, 15000); // 15 seconds polling for fallback
    return () => clearInterval(interval);
  }, [user, queryClient]);

  const NotificationItem = ({ notification }: { notification: Notification }) => (
    <div
      className={cn(
        "flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer group",
        !notification.is_read && "bg-muted/30",
      )}
      onClick={() => {
        if (!notification.is_read) {
          markAsRead(notification.id);
        }
      }}
    >
      <div className="mt-1 shrink-0 rounded-full bg-background p-1.5 shadow-sm border border-border">
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 space-y-1 overflow-hidden">
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
      {!notification.is_read && (
        <div className="shrink-0 flex items-center">
          <div className="h-2 w-2 rounded-full bg-primary" />
        </div>
      )}
    </div>
  );

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          className="relative grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
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
        <Tabs defaultValue="all" className="w-full">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface">
            <TypoHeading as="h2">Notifications</TypoHeading>
            <div className="flex items-center gap-2">
              <TabsList className="h-8">
                <TabsTrigger value="all" className="text-xs px-3">
                  All
                </TabsTrigger>
                <TabsTrigger value="unread" className="text-xs px-3">
                  Unread
                  {unreadCount > 0 && (
                    <span className="ml-1.5 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                      {unreadCount}
                    </span>
                  )}
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
                Mark all as read
              </Button>
            )}
          </div>

          <ScrollArea className="h-[400px]">
            <TabsContent
              value="all"
              className="m-0 focus-visible:outline-none focus-visible:ring-0"
            >
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <Bell className="h-8 w-8 mb-2 opacity-20" />
                  <p className="text-sm">No notifications yet</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-border/50">
                  {notifications.map((notification) => (
                    <NotificationItem key={notification.id} notification={notification} />
                  ))}
                </div>
              )}
            </TabsContent>
            <TabsContent
              value="unread"
              className="m-0 focus-visible:outline-none focus-visible:ring-0"
            >
              {notifications.filter((n) => !n.is_read).length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <CheckCircle className="h-8 w-8 mb-2 opacity-20 text-emerald-500" />
                  <p className="text-sm">You're all caught up!</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-border/50">
                  {notifications
                    .filter((n) => !n.is_read)
                    .map((notification) => (
                      <NotificationItem key={notification.id} notification={notification} />
                    ))}
                </div>
              )}
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </PopoverContent>
    </Popover>
  );
}
