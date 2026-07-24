import React, { useState } from "react";
import { 
  Bell, 
  Check, 
  CheckCircle, 
  FolderPlus, 
  MessageCircle, 
  MessageSquare, 
  Users, 
  XCircle,
  AtSign
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NotificationType = 
  | "project_invitation" 
  | "team_request" 
  | "comment" 
  | "mention" 
  | "application_accepted" 
  | "application_rejected" 
  | "message_received";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  description: string;
  createdAt: Date;
  read: boolean;
  avatar?: string;
}

const mockNotifications: Notification[] = [
  {
    id: "1",
    type: "project_invitation",
    title: "Project Invitation",
    description: "Sarah invited you to join the 'Next.js E-commerce' project.",
    createdAt: new Date(Date.now() - 1000 * 60 * 5),
    read: false,
  },
  {
    id: "2",
    type: "mention",
    title: "Mentioned you",
    description: "Alex mentioned you in a comment: '@johndoe can you review this?'",
    createdAt: new Date(Date.now() - 1000 * 60 * 30),
    read: false,
  },
  {
    id: "3",
    type: "team_request",
    title: "Team Request",
    description: "David wants to join your 'DevLink' team.",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
    read: false,
  },
  {
    id: "4",
    type: "application_accepted",
    title: "Application Accepted",
    description: "Your application for 'Senior React Developer' was accepted!",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
    read: true,
  },
  {
    id: "5",
    type: "comment",
    title: "New Comment",
    description: "Emily commented on your post 'State Management in 2024'.",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
    read: true,
  },
  {
    id: "6",
    type: "application_rejected",
    title: "Application Status Update",
    description: "Unfortunately, your application for 'UI Designer' was not selected.",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
    read: true,
  },
  {
    id: "7",
    type: "message_received",
    title: "New Message",
    description: "Michael sent you a message: 'Hey, are you available for a quick chat?'",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 96),
    read: true,
  },
];

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case "project_invitation":
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
    case "message_received":
      return <MessageSquare className="h-4 w-4 text-sky-500" />;
  }
};

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [isOpen, setIsOpen] = useState(false);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications(notifications.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const NotificationItem = ({ notification }: { notification: Notification }) => (
    <div
      className={cn(
        "flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer group",
        !notification.read && "bg-muted/30"
      )}
      onClick={() => markAsRead(notification.id)}
    >
      <div className="mt-1 shrink-0 rounded-full bg-background p-1.5 shadow-sm border border-border">
        {getNotificationIcon(notification.type)}
      </div>
      <div className="flex-1 space-y-1 overflow-hidden">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium leading-none text-foreground truncate">
            {notification.title}
          </p>
          <span className="text-xs text-muted-foreground whitespace-nowrap shrink-0">
            {formatDistanceToNow(notification.createdAt, { addSuffix: true })}
          </span>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {notification.description}
        </p>
      </div>
      {!notification.read && (
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
            <h2 className="text-sm font-semibold text-foreground">Notifications</h2>
            <div className="flex items-center gap-2">
              <TabsList className="h-8">
                <TabsTrigger value="all" className="text-xs px-3">All</TabsTrigger>
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
            <span className="text-xs text-muted-foreground font-medium">
              You have {unreadCount} unread notifications
            </span>
            {unreadCount > 0 && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 text-xs px-2 text-muted-foreground hover:text-foreground"
                onClick={markAllAsRead}
              >
                <Check className="mr-1.5 h-3 w-3" />
                Mark all as read
              </Button>
            )}
          </div>

          <ScrollArea className="h-[400px]">
            <TabsContent value="all" className="m-0 focus-visible:outline-none focus-visible:ring-0">
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
            <TabsContent value="unread" className="m-0 focus-visible:outline-none focus-visible:ring-0">
              {notifications.filter((n) => !n.read).length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <CheckCircle className="h-8 w-8 mb-2 opacity-20 text-emerald-500" />
                  <p className="text-sm">You're all caught up!</p>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-border/50">
                  {notifications
                    .filter((n) => !n.read)
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
