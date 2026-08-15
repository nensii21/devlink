import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import {
  MessageSquare,
  FolderKanban,
  Building2,
  AtSign,
  ShieldAlert,
  Megaphone,
} from "lucide-react";

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
              Preferences are grouped by category so you can quickly find and manage the alerts that
              matter to you.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion
              type="multiple"
              defaultValue={[
                "messages",
                "projects",
                "organizations",
                "mentions",
                "security",
                "marketing",
              ]}
              className="w-full"
            >
              {/* Messages */}
              <AccordionItem value="messages">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <MessageSquare className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Messages</div>
                      <TypoCaption as="p">
                        Direct messages and replies in your active conversations.
                      </TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">New messages</Label>
                        <TypoCaption as="p">
                          Get notified when someone sends you a direct message.
                        </TypoCaption>
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
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Projects */}
              <AccordionItem value="projects">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <FolderKanban className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Projects</div>
                      <TypoCaption as="p">
                        Milestones, status changes, and repository activity.
                      </TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">Project updates</Label>
                        <TypoCaption as="p">
                          Milestones reached, status changes, and repository activity on your
                          projects.
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
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Organizations */}
              <AccordionItem value="organizations">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Organizations</div>
                      <TypoCaption as="p">
                        Team invitations, membership, and role changes.
                      </TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between pb-4 border-b border-border/40">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">Team invitations</Label>
                        <TypoCaption as="p">
                          When you're invited to join a team or project.
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

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">Role changes</Label>
                        <TypoCaption as="p">
                          When your permissions or role within an organization are updated.
                        </TypoCaption>
                      </div>
                      <Switch
                        checked={formData.role_changes}
                        onCheckedChange={() => handleToggle("role_changes")}
                      />
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Mentions */}
              <AccordionItem value="mentions">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <AtSign className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Mentions</div>
                      <TypoCaption as="p">When someone tags or mentions you directly.</TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">@mentions</Label>
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
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Security */}
              <AccordionItem value="security">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Security</div>
                      <TypoCaption as="p">
                        Platform announcements and critical account alerts.
                      </TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between pb-4 border-b border-border/40">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">System announcements</Label>
                        <TypoCaption as="p">
                          Platform updates and scheduled maintenance windows.
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

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">Security alerts</Label>
                        <TypoCaption as="p">
                          Critical security notifications about your account. Always on.
                        </TypoCaption>
                      </div>
                      <Switch
                        checked={formData.system_alerts}
                        onCheckedChange={() => handleToggle("system_alerts")}
                        disabled={true}
                      />
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Marketing */}
              <AccordionItem value="marketing" className="border-b-0">
                <AccordionTrigger>
                  <div className="flex items-center gap-3">
                    <Megaphone className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="space-y-0.5 text-left">
                      <div className="text-base font-semibold">Marketing</div>
                      <TypoCaption as="p">Product news and promotional emails.</TypoCaption>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pl-7">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label className="text-sm font-medium">Marketing & news</Label>
                        <TypoCaption as="p">
                          Occasional updates about new DevLink features and tips.
                        </TypoCaption>
                      </div>
                      <Switch
                        checked={formData.marketing_emails}
                        onCheckedChange={() => handleToggle("marketing_emails")}
                      />
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
