import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/settings/notifications")({
  component: NotificationSettingsPage,
});

/**
 * Every preference the server stores, all booleans. Kept as a partial on the
 * read side because the server may add keys ahead of the client knowing them.
 */
type NotificationPreferences = Record<string, boolean>;

function NotificationSettingsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: preferences, isLoading } = useQuery({
    queryKey: ["notification-preferences"],
    // api.get resolves to the parsed body; there is no `.data` envelope, and
    // unwrapping one meant the form always rendered its defaults instead of
    // the user's saved settings.
    queryFn: async () => {
      const res = await api.get("/api/notifications/preferences");
      return res;
    },
  });

  const [formData, setFormData] = useState({
    email_enabled: true,
    websocket_enabled: true,
    database_enabled: true,
    messages: true,
    team_invitations: true,
    project_updates: true,
    mentions: true,
    system_announcements: true,
    email_messages: true,
    email_team_invitations: true,
    email_project_updates: true,
    email_mentions: true,
    email_system_announcements: true,
    invitations: true,
    role_changes: true,
    marketing_emails: false,
    system_alerts: true,
  });

  useEffect(() => {
    if (preferences) {
      setFormData((prev) => ({ ...prev, ...preferences }));
    }
  }, [preferences]);

  const updateMutation = useMutation({
    mutationFn: async (newData: typeof formData) => {
      await api.put("/api/notifications/preferences", newData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
      toast({
        title: "Preferences updated",
        description: "Your notification settings have been saved successfully.",
      });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update preferences.",
      });
    },
  });

  const handleToggle = (key: keyof typeof formData) => {
    const newData = { ...formData, [key]: !formData[key] };
    setFormData(newData);
    updateMutation.mutate(newData);
  };

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto p-6">
        <div>
          <Skeleton className="h-8 w-64 animate-pulse" />
          <Skeleton className="mt-2 h-4 w-96 animate-pulse" />
        </div>
        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-36 animate-pulse" />
              <Skeleton className="mt-1.5 h-4 w-72 animate-pulse" />
            </CardHeader>
            <CardContent className="space-y-6">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="flex items-center justify-between border-b border-border/40 pb-4 last:border-0 last:pb-0"
                >
                  <div className="space-y-1.5">
                    <Skeleton className="h-4 w-28 animate-pulse" />
                    <Skeleton className="h-3 w-48 animate-pulse" />
                  </div>
                  <Skeleton className="h-6 w-11 rounded-full animate-pulse" />
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      <div>
        <TypoHeading as="h2">Notification Preferences Center</TypoHeading>
        <TypoCaption as="p">
          Manage your notification channels, category alerts, and email delivery preferences.
        </TypoCaption>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Delivery Channels</CardTitle>
            <CardDescription>
              Master controls for global notification delivery methods.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Master Email Notifications</Label>
                <TypoCaption as="p">
                  Master switch to enable or disable all email notifications.
                </TypoCaption>
              </div>
              <Switch
                checked={formData.email_enabled}
                onCheckedChange={() => handleToggle("email_enabled")}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">In-App Notifications</Label>
                <TypoCaption as="p">
                  Store notifications in your notification center tray.
                </TypoCaption>
              </div>
              <Switch
                checked={formData.database_enabled}
                onCheckedChange={() => handleToggle("database_enabled")}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Real-time Popups (WebSocket)</Label>
                <TypoCaption as="p">
                  Receive instant desktop toast popups while actively using DevLink.
                </TypoCaption>
              </div>
              <Switch
                checked={formData.websocket_enabled}
                onCheckedChange={() => handleToggle("websocket_enabled")}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notification Categories</CardTitle>
            <CardDescription>
              Configure in-app and email preferences for specific notification categories.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Messages */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Messages</Label>
                <TypoCaption as="p">Direct messages and active conversation alerts.</TypoCaption>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">In-App</Label>
                  <Switch
                    checked={formData.messages}
                    onCheckedChange={() => handleToggle("messages")}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Switch
                    checked={formData.email_messages}
                    onCheckedChange={() => handleToggle("email_messages")}
                    disabled={!formData.email_enabled}
                  />
                </div>
              </div>
            </div>

            {/* Team Invitations */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Team Invitations</Label>
                <TypoCaption as="p">
                  Project invites, team membership, and role changes.
                </TypoCaption>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">In-App</Label>
                  <Switch
                    checked={formData.team_invitations}
                    onCheckedChange={() => handleToggle("team_invitations")}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Switch
                    checked={formData.email_team_invitations}
                    onCheckedChange={() => handleToggle("email_team_invitations")}
                    disabled={!formData.email_enabled}
                  />
                </div>
              </div>
            </div>

            {/* Project Updates */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Project Updates</Label>
                <TypoCaption as="p">
                  Milestones, project status changes, and repository activity.
                </TypoCaption>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">In-App</Label>
                  <Switch
                    checked={formData.project_updates}
                    onCheckedChange={() => handleToggle("project_updates")}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Switch
                    checked={formData.email_project_updates}
                    onCheckedChange={() => handleToggle("email_project_updates")}
                    disabled={!formData.email_enabled}
                  />
                </div>
              </div>
            </div>

            {/* Mentions */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Mentions</Label>
                <TypoCaption as="p">
                  When developers tag or mention @username in issues or discussions.
                </TypoCaption>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">In-App</Label>
                  <Switch
                    checked={formData.mentions}
                    onCheckedChange={() => handleToggle("mentions")}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Switch
                    checked={formData.email_mentions}
                    onCheckedChange={() => handleToggle("email_mentions")}
                    disabled={!formData.email_enabled}
                  />
                </div>
              </div>
            </div>

            {/* System Announcements */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">System Announcements</Label>
                <TypoCaption as="p">
                  Platform updates, scheduled maintenance, and system alerts.
                </TypoCaption>
              </div>
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">In-App</Label>
                  <Switch
                    checked={formData.system_announcements}
                    onCheckedChange={() => handleToggle("system_announcements")}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <Switch
                    checked={formData.email_system_announcements}
                    onCheckedChange={() => handleToggle("email_system_announcements")}
                    disabled={!formData.email_enabled}
                  />
                </div>
              </div>
            </div>

            {/* Role Changes */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Role Changes</Label>
                <TypoCaption as="p">When your permissions or roles are modified.</TypoCaption>
              </div>
              <Switch
                checked={formData.role_changes}
                onCheckedChange={() => handleToggle("role_changes")}
              />
            </div>

            {/* System Alerts */}
            <div className="flex items-center justify-between pb-4 border-b">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">System Alerts</Label>
                <TypoCaption as="p">Critical security and system notifications.</TypoCaption>
              </div>
              <Switch
                checked={formData.system_alerts}
                onCheckedChange={() => handleToggle("system_alerts")}
                disabled={true}
              />
            </div>

            {/* Marketing & News */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Marketing & News</Label>
                <TypoCaption as="p">Occasional updates about DevLink features.</TypoCaption>
              </div>
              <Switch
                checked={formData.marketing_emails}
                onCheckedChange={() => handleToggle("marketing_emails")}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
