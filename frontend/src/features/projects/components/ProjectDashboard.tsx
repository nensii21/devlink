import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import { Card, TagChip, Avatar, Skeleton } from "@/components/shared/primitives";
import {
  Calendar,
  Bell,
  Users2,
  CheckCircle2,
  Clock,
  Plus,
  TrendingUp,
  MessageSquare,
  Activity,
  ArrowRight,
  Shield,
  Loader2,
  Check,
  AlertCircle,
  Flag,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { TypoSection, TypoCaption, TypoCard, TypoHeading } from "@/components/shared/Typography";

interface DashboardMember {
  user_id: string;
  username: string;
  full_name: string | null;
  profile_image: string | null;
  role: string;
  is_online: boolean;
  last_seen: string | null;
}

interface DashboardInvitation {
  user_id: string;
  username: string;
  full_name: string | null;
  profile_image: string | null;
  role: string;
  invited_at: string;
}

interface Milestone {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  is_completed: boolean;
  created_at: string;
}

interface Announcement {
  id: string;
  project_id: string;
  author_id: string;
  title: string;
  content: string;
  created_at: string;
  author: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
    profile_image: string | null;
  };
}

interface ActivityItem {
  id: string;
  actor_id: string;
  activity_type: string;
  title: string;
  description: string | null;
  created_at: string;
  actor: {
    username: string;
    profile_image: string | null;
  } | null;
}

interface ProjectDashboardData {
  project_id: string;
  title: string;
  stage: string;
  recent_activity: ActivityItem[];
  milestones: Milestone[];
  announcements: Announcement[];
  members: DashboardMember[];
  pending_invitations: DashboardInvitation[];
}

interface ProjectDashboardProps {
  projectId: string;
  currentUserRole: string; // "owner", "co_owner", "admin", "maintainer", "member", or "" (non-member)
}

export const ProjectDashboard: React.FC<ProjectDashboardProps> = ({
  projectId,
  currentUserRole,
}) => {
  const queryClient = useQueryClient();

  // Tabs & Form Modals States
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [showAnnouncementModal, setShowAnnouncementModal] = useState(false);

  // New Milestone Form State
  const [mTitle, setMTitle] = useState("");
  const [mDescription, setMDescription] = useState("");
  const [mDueDate, setMDueDate] = useState("");

  // New Announcement Form State
  const [aTitle, setATitle] = useState("");
  const [aContent, setAContent] = useState("");

  // Query Dashboard Data
  const {
    data: d,
    isLoading,
    error,
  } = useQuery<ProjectDashboardData>({
    queryKey: ["projectDashboard", projectId],
    queryFn: () => api.get<ProjectDashboardData>(`/projects/${projectId}/dashboard`),
    retry: false,
  });

  // Check write access based on project permissions
  const hasWriteAccess = ["owner", "co_owner", "admin", "maintainer"].includes(
    currentUserRole.toLowerCase(),
  );

  // Mutations
  const createMilestoneMutation = useMutation({
    mutationFn: (payload: { title: string; description: string; due_date: string | null }) =>
      api.post<Milestone>(`/projects/${projectId}/milestones`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectDashboard", projectId] });
      toast.success("Milestone created successfully!");
      setShowMilestoneModal(false);
      setMTitle("");
      setMDescription("");
      setMDueDate("");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to create milestone.");
    },
  });

  const toggleMilestoneMutation = useMutation({
    mutationFn: ({ milestoneId, completed }: { milestoneId: string; completed: boolean }) =>
      api.patch<Milestone>(
        `/projects/${projectId}/milestones/${milestoneId}/complete?is_completed=${completed}`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectDashboard", projectId] });
      toast.success("Milestone status updated!");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update milestone status.");
    },
  });

  const createAnnouncementMutation = useMutation({
    mutationFn: (payload: { title: string; content: string }) =>
      api.post<Announcement>(`/projects/${projectId}/announcements`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectDashboard", projectId] });
      toast.success("Announcement posted!");
      setShowAnnouncementModal(false);
      setATitle("");
      setAContent("");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to post announcement.");
    },
  });

  const updateStageMutation = useMutation({
    mutationFn: (stage: string) => api.put(`/projects/${projectId}`, { stage }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectDashboard", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      toast.success("Project stage updated!");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to update project stage.");
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-20 w-full rounded-lg" />
        <div className="grid gap-6 md:grid-cols-3">
          <Skeleton className="h-64 md:col-span-2 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !d) {
    return (
      <Card className="flex flex-col items-center justify-center p-8 text-center border-dashed border-2 border-destructive/20 bg-destructive/5">
        <AlertCircle className="h-12 w-12 text-destructive mb-3" />
        <TypoSection>Workspace Locked</TypoSection>
        <TypoCaption as="p">
          You must be an active project team member to access this private workspace dashboard.
        </TypoCaption>
      </Card>
    );
  }

  // Calculate milestone progress
  const totalMilestones = d.milestones.length;
  const completedMilestones = d.milestones.filter((m) => m.is_completed).length;
  const milestoneProgress =
    totalMilestones > 0 ? Math.round((completedMilestones / totalMilestones) * 100) : 0;

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "project_milestone":
        return <Flag className="h-4 w-4 text-success" />;
      case "project_announcement":
        return <Bell className="h-4 w-4 text-info" />;
      case "project_created":
      case "project_updated":
        return <TrendingUp className="h-4 w-4 text-primary" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Centralized Stage Banner & Team Stats */}
      <Card className="relative overflow-hidden bg-gradient-to-r from-surface to-muted/20 p-6 border border-border/80">
        <div className="absolute top-0 right-0 h-32 w-32 bg-primary/5 rounded-full blur-2xl pointer-events-none" />
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-success animate-pulse" />
              <TypoHeading as="h2">Team Workspace Dashboard</TypoHeading>
            </div>
            <TypoCaption as="p">
              Centralized project status, announcements, and milestones.
            </TypoCaption>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {/* Project Stage Quick Action */}
            <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5 shadow-sm">
              <TypoCaption>Project Stage:</TypoCaption>
              {hasWriteAccess ? (
                <select
                  value={d.stage}
                  onChange={(e) => updateStageMutation.mutate(e.target.value)}
                  className="bg-transparent text-xs font-bold text-foreground border-none outline-none focus:ring-0 cursor-pointer"
                  disabled={updateStageMutation.isPending}
                >
                  <option value="idea">Idea</option>
                  <option value="validation">Validation</option>
                  <option value="mvp">MVP</option>
                  <option value="beta">Beta</option>
                  <option value="production">Production</option>
                </select>
              ) : (
                <TagChip className="text-xs font-bold bg-primary/10 text-primary capitalize">
                  {d.stage}
                </TagChip>
              )}
            </div>

            {/* Quick Actions Buttons */}
            {hasWriteAccess && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowMilestoneModal(true)}
                  className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow transition hover:opacity-90"
                >
                  <Plus size={14} /> Milestone
                </button>
                <button
                  onClick={() => setShowAnnouncementModal(true)}
                  className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-foreground shadow-sm transition hover:bg-muted"
                >
                  <Plus size={14} /> Announcement
                </button>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Main Workspace Dashboard Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Columns: Milestones, Announcements, and Activity */}
        <div className="lg:col-span-2 space-y-6">
          {/* Milestone checklist widget */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                <TypoSection>Upcoming Milestones</TypoSection>
              </div>
              <span className="text-xs font-semibold bg-muted px-2 py-1 rounded">
                {completedMilestones} / {totalMilestones} Completed
              </span>
            </div>

            {totalMilestones > 0 ? (
              <div className="space-y-3">
                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Overall Progress</span>
                    <span>{milestoneProgress}%</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500"
                      style={{ width: `${milestoneProgress}%` }}
                    />
                  </div>
                </div>

                {/* Milestone list */}
                <ul className="divide-y divide-border/60">
                  {d.milestones.map((m) => (
                    <li key={m.id} className="flex items-start gap-3 py-3 group">
                      <input
                        type="checkbox"
                        checked={m.is_completed}
                        onChange={(e) =>
                          toggleMilestoneMutation.mutate({
                            milestoneId: m.id,
                            completed: e.target.checked,
                          })
                        }
                        disabled={!hasWriteAccess || toggleMilestoneMutation.isPending}
                        className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary cursor-pointer disabled:opacity-50"
                      />
                      <div className="min-w-0 flex-1">
                        <p
                          className={cn(
                            "text-sm font-semibold text-foreground transition-all",
                            m.is_completed && "line-through text-muted-foreground",
                          )}
                        >
                          {m.title}
                        </p>
                        {m.description && (
                          <TypoCaption as="p">{m.description}</TypoCaption>
                        )}
                        {m.due_date && (
                          <TypoCaption>
                            <Clock size={10} /> Due {new Date(m.due_date).toLocaleDateString()}
                          </TypoCaption>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="text-center py-8 border border-dashed rounded-lg border-border/60">
                <Flag className="h-8 w-8 text-muted-foreground/60 mx-auto mb-2" />
                <TypoCaption as="p">No team milestones scheduled.</TypoCaption>
              </div>
            )}
          </Card>

          {/* Announcements Widget */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" />
              <TypoSection>Announcements</TypoSection>
            </div>

            {d.announcements.length > 0 ? (
              <div className="space-y-4">
                {d.announcements.map((ann) => (
                  <div
                    key={ann.id}
                    className="p-4 rounded-lg bg-muted/20 border border-border/50 space-y-2"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <TypoCard>{ann.title}</TypoCard>
                        <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                          <span>
                            By {ann.author.first_name} {ann.author.last_name}
                          </span>
                          <span>•</span>
                          <span>{new Date(ann.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <Avatar
                        src={ann.author.profile_image || undefined}
                        alt={ann.author.username}
                        size={24}
                      />
                    </div>
                    <TypoCaption as="p">
                      {ann.content}
                    </TypoCaption>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 border border-dashed rounded-lg border-border/60">
                <Bell className="h-8 w-8 text-muted-foreground/60 mx-auto mb-2" />
                <TypoCaption as="p">No recent team announcements.</TypoCaption>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Active Members, Pending Invites, and Recent Activity */}
        <div className="space-y-6">
          {/* Team Members List */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-border/60 pb-3">
              <Users2 className="h-4 w-4 text-primary" />
              <TypoSection>Active Team</TypoSection>
            </div>

            <ul className="space-y-3">
              {d.members.map((m) => (
                <li key={m.user_id} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <Avatar
                      src={m.profile_image || undefined}
                      alt={m.username}
                      size={32}
                      online={m.is_online}
                    />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground leading-tight truncate">
                        {m.full_name || m.username}
                      </p>
                      <TypoCaption as="p">@{m.username}</TypoCaption>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-0.5 text-[9px] font-bold uppercase tracking-wider text-primary/80 bg-primary/5 border border-primary/10 px-1.5 py-0.5 rounded">
                    {m.role === "owner" && <Shield size={8} className="text-primary mr-0.5" />}
                    {m.role}
                  </span>
                </li>
              ))}
            </ul>

            {/* Pending invites */}
            {d.pending_invitations.length > 0 && (
              <div className="pt-4 border-t border-border/60 space-y-3">
                <TypoCaption as="p">
                  Pending Invitations ({d.pending_invitations.length})
                </TypoCaption>
                <ul className="space-y-3">
                  {d.pending_invitations.map((invite) => (
                    <li
                      key={invite.user_id}
                      className="flex items-center justify-between gap-2 opacity-75"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar
                          src={invite.profile_image || undefined}
                          alt={invite.username}
                          size={28}
                        />
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-foreground truncate">
                            {invite.full_name || invite.username}
                          </p>
                          <TypoCaption as="p">@{invite.username}</TypoCaption>
                        </div>
                      </div>
                      <TypoCaption>Pending</TypoCaption>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          {/* Activity Timeline widget */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-border/60 pb-3">
              <Activity className="h-4 w-4 text-primary" />
              <TypoSection>Recent Activity</TypoSection>
            </div>

            {d.recent_activity.length > 0 ? (
              <div className="relative pl-4 space-y-4 before:absolute before:left-[7px] before:top-1.5 before:bottom-1.5 before:w-0.5 before:bg-border/60">
                {d.recent_activity.slice(0, 10).map((act) => (
                  <div
                    key={act.id}
                    className="relative flex gap-2.5 text-xs text-muted-foreground leading-normal"
                  >
                    <span className="absolute -left-[18px] top-0.5 bg-surface rounded-full p-0.5 border border-border shadow-sm">
                      {getActivityIcon(act.activity_type)}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground">{act.title}</p>
                      {act.description && <p className="text-[10px] mt-0.5">{act.description}</p>}
                      <TypoCaption>
                        {new Date(act.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}{" "}
                        · {new Date(act.created_at).toLocaleDateString()}
                      </TypoCaption>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <TypoCaption as="p">
                No recent team activities.
              </TypoCaption>
            )}
          </Card>
        </div>
      </div>

      {/* Form Modals */}
      {/* Create Milestone Modal */}
      {showMilestoneModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <Card className="w-full max-w-md p-6 space-y-4 relative border border-border shadow-lg">
            <div className="flex items-center justify-between border-b pb-3">
              <TypoSection>Create Milestone</TypoSection>
              <button
                onClick={() => setShowMilestoneModal(false)}
                className="text-muted-foreground hover:text-foreground transition"
              >
                ✕
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMilestoneMutation.mutate({
                  title: mTitle,
                  description: mDescription,
                  due_date: mDueDate || null,
                });
              }}
              className="space-y-4"
            >
              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Milestone Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Release Beta 1.0"
                  value={mTitle}
                  onChange={(e) => setMTitle(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Description
                </label>
                <textarea
                  placeholder="Briefly describe what this milestone covers..."
                  value={mDescription}
                  onChange={(e) => setMDescription(e.target.value)}
                  rows={3}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none resize-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Due Date
                </label>
                <input
                  type="datetime-local"
                  value={mDueDate}
                  onChange={(e) => setMDueDate(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 border-t pt-3">
                <button
                  type="button"
                  onClick={() => setShowMilestoneModal(false)}
                  className="rounded-md border border-border px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMilestoneMutation.isPending}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow transition hover:opacity-90 disabled:opacity-50"
                >
                  {createMilestoneMutation.isPending && (
                    <Loader2 size={12} className="animate-spin" />
                  )}
                  Create Milestone
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Create Announcement Modal */}
      {showAnnouncementModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <Card className="w-full max-w-md p-6 space-y-4 relative border border-border shadow-lg">
            <div className="flex items-center justify-between border-b pb-3">
              <TypoSection>Post Announcement</TypoSection>
              <button
                onClick={() => setShowAnnouncementModal(false)}
                className="text-muted-foreground hover:text-foreground transition"
              >
                ✕
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createAnnouncementMutation.mutate({
                  title: aTitle,
                  content: aContent,
                });
              }}
              className="space-y-4"
            >
              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Weekly Sync Rescheduled"
                  value={aTitle}
                  onChange={(e) => setATitle(e.target.value)}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground uppercase">
                  Content
                </label>
                <textarea
                  required
                  placeholder="e.g. Our weekly kickoff is rescheduled to 2 PM EST due to..."
                  value={aContent}
                  onChange={(e) => setAContent(e.target.value)}
                  rows={4}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 border-t pt-3">
                <button
                  type="button"
                  onClick={() => setShowAnnouncementModal(false)}
                  className="rounded-md border border-border px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAnnouncementMutation.isPending}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow transition hover:opacity-90 disabled:opacity-50"
                >
                  {createAnnouncementMutation.isPending && (
                    <Loader2 size={12} className="animate-spin" />
                  )}
                  Post Announcement
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};