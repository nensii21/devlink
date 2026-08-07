import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useQuery, useMutation } from "@tanstack/react-query";
import { projectsService } from "@/services";
import { Card, TagChip, Avatar, Skeleton } from "@/components/shared/primitives";
import { api } from "@/api";
import { ProjectDashboard } from "@/features/projects/components/ProjectDashboard";
import { CollaborativeWorkspace } from "@/components/projects/CollaborativeWorkspace";
import { ProjectMembersList } from "@/features/projects/components/ProjectMembersList";
import {
  ArrowLeft,
  Star,
  GitFork,
  Users2,
  Github,
  Copy,
  Check,
  Eye,
  Sparkles,
  X,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { builders, activity, currentUser } from "@/mocks/seed";
import { Markdown } from "@/components/shared/Markdown";
import { BackButton } from "@/components/shared/BackButton";
import { ShareProjectButton } from "@/components/shared/ShareProjectButton";
import { projectTagsApi } from "@/api";
import { type TagSuggestion } from "@/api/modules/projectTags";
import { toast } from "sonner";
import { BookmarkToggleButton } from "@/components/shared/BookmarkToggleButton";
import { addRecentlyViewedProject } from "@/lib/recentlyViewedProjects";

import { usePermissions } from "@/hooks/usePermissions";
import { ProjectTimeline } from "@/components/project/ProjectTimeline";
import { ProjectInsightsCard } from "@/components/projects/ProjectInsightsCard";

export const Route = createFileRoute("/_app/projects/$projectId")({
  head: ({ params }) => ({
    meta: [
      { title: `${params.projectId} — DevLink` },
      { name: "description", content: "Project details, members, activity and repositories." },
    ],
  }),
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const { data: p, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsService.get(projectId),
  });
  const [tab, setTab] = useState<
    "overview" | "workspace" | "members" | "activity" | "repos" | "dashboard"
  >("overview");
  const [copied, setCopied] = useState(false);
  const isOwner = p?.owner === currentUser.name;

  const { data: dashboard } = useQuery({
    queryKey: ["projectDashboard", projectId],
    queryFn: () =>
      api.get<{ members: { user_id: string; username: string; role: string }[] }>(
        `/projects/${projectId}/dashboard`,
      ),
    retry: false,
    enabled: !!p,
  });

  const memberObj = dashboard?.members?.find(
    (m) => m.user_id === currentUser.id || m.username === currentUser.name,
  );
  const currentUserRole = isOwner ? "owner" : memberObj?.role || "";

  // Tag generator state
  const [showTagGenerator, setShowTagGenerator] = useState(false);
  const [suggestedTags, setSuggestedTags] = useState<TagSuggestion[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const tagMutation = useMutation({
    mutationFn: () =>
      projectTagsApi.generate({
        title: p?.name || "",
        description: p?.description || "",
        tech_stack: p?.stack?.join(", "),
      }),
    onSuccess: (data) => {
      setSuggestedTags(data.tags);
      setSelectedTags(data.tags.map((t) => t.name));
    },
    onError: (err) => {
      const msg = err instanceof Error ? err.message : "Please try again.";
      toast.error(`Failed to generate tags. ${msg}`);
      setSuggestedTags([]);
    },
  });

  // Integrate RBAC hook
  const { can } = usePermissions(currentUser.id || "current-user-uuid");
  const hasInvitePermission = can("project:invite", {
    ownerId: p?.ownerId,
  });

  const toggleTag = (tagName: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagName) ? prev.filter((t) => t !== tagName) : [...prev, tagName],
    );
  };

  const handleCopyInviteLink = async () => {
    const inviteLink = `${window.location.origin}/projects/${projectId}?invite=true`;

    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);

    window.setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) return <Card className="h-96 animate-pulse" />;
  if (!p) throw notFound();

  const tabs = dashboard
    ? (["overview", "workspace", "members", "activity", "repos", "dashboard"] as const)
    : (["overview", "workspace", "members", "activity", "repos"] as const);

  return (
    <div className="space-y-4">
      <BackButton to="/projects" label="Back to projects" />
      <Card className="p-5">
        <div className="flex items-start gap-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-md bg-muted text-3xl">
            {p.icon}
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-[22px] font-bold text-foreground">{p.name}</h1>
            <p className="mt-1 text-[13px] text-muted-foreground">{p.description}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {p.stack.map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {isOwner && (
              <button
                type="button"
                onClick={handleCopyInviteLink}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-muted"
                aria-label="Copy project invitation link"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy invite link"}
              </button>
            )}

            <ShareProjectButton projectTitle={p.name} projectDescription={p.description} />

            <BookmarkToggleButton projectId={p.id} />

            <div className="hidden gap-4 text-[12px] text-muted-foreground sm:flex">
              <span className="inline-flex items-center gap-1">
                <Star size={12} /> {p.stars}
              </span>
              <span className="inline-flex items-center gap-1">
                <Eye size={12} /> {p.views}
              </span>
              <span className="inline-flex items-center gap-1">
                <GitFork size={12} /> {p.forks}
              </span>
              <span className="inline-flex items-center gap-1">
                <Users2 size={12} /> {p.members}
              </span>
            </div>
          </div>
        </div>
      </Card>

      <div className="flex items-center gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "border-b-2 px-3 py-2 text-[13px] font-medium capitalize transition-colors",
              tab === t
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t === "dashboard" ? "Team Workspace" : t}
          </button>
        ))}
        <Link
          to="/projects/$projectId/issues"
          params={{ projectId }}
          className="border-b-2 border-transparent px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Issues
        </Link>
      </div>

      {tab === "overview" && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="p-4 lg:col-span-2">
            <p className="text-[13px] font-semibold text-foreground">About</p>
            <Markdown content={p.description} className="mt-2 text-muted-foreground" />
            <p className="mt-4 text-[13px] font-semibold text-foreground">Progress</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary" style={{ width: `${p.progress}%` }} />
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">{p.progress}% complete</p>
          </Card>
          <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">Owner</p>
            <p className="mt-2 text-[13px] text-muted-foreground">{p.owner}</p>
            <p className="mt-4 text-[13px] font-semibold text-foreground">Status</p>
            <p className="mt-1 text-[13px] capitalize text-muted-foreground">{p.status}</p>

            {/* AI Tag Generator Section */}
            <div className="mt-4 border-t border-border pt-4">
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-semibold text-foreground flex items-center gap-2">
                  <Sparkles size={14} className="text-primary" />
                  AI Tags
                </p>
                {!showTagGenerator && (
                  <button
                    onClick={() => {
                      setShowTagGenerator(true);
                      if (suggestedTags.length === 0) {
                        tagMutation.mutate();
                      }
                    }}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                  >
                    Generate
                  </button>
                )}
              </div>

              {showTagGenerator && (
                <div className="mt-3">
                  {tagMutation.isPending ? (
                    <div className="space-y-2">
                      <Skeleton className="h-6 w-full" />
                      <Skeleton className="h-6 w-3/4" />
                      <Skeleton className="h-6 w-1/2" />
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-1.5">
                        {suggestedTags.map((tag) => (
                          <button
                            key={tag.name}
                            onClick={() => toggleTag(tag.name)}
                            className={cn(
                              "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium transition-colors",
                              selectedTags.includes(tag.name)
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-border bg-surface text-muted-foreground hover:border-primary/50",
                            )}
                          >
                            {tag.name}
                            <span className="text-[9px] opacity-60">
                              {Math.round(tag.confidence * 100)}%
                            </span>
                          </button>
                        ))}
                      </div>
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] text-muted-foreground">
                          {selectedTags.length} tags selected
                        </p>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => tagMutation.mutate()}
                            className="rounded-md px-2 py-1 text-[10px] text-muted-foreground hover:bg-muted/50"
                          >
                            Regenerate
                          </button>
                          <button
                            onClick={() => {
                              toast.success(`Selected ${selectedTags.length} tags`);
                              setShowTagGenerator(false);
                            }}
                            className="rounded-md bg-primary px-2 py-1 text-[10px] font-semibold text-primary-foreground hover:opacity-90"
                          >
                            Apply
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>

          <Card className="p-4 lg:col-span-3">
            <ProjectInsightsCard
              projectId={projectId}
              title={p.name}
              description={p.description}
              techStack={p.stack}
              status={p.status}
              members={p.members}
            />
          </Card>

          <ProjectTimeline className="mt-6 lg:col-span-3" />
        </div>
      )}
      {tab === "members" && (
        <Card className="p-6">
          <ProjectMembersList
            projectId={projectId}
            currentUserId={currentUser.id}
            isOwner={isOwner}
          />
        </Card>
      )}
      {tab === "activity" && (
        <Card>
          <ul className="divide-y divide-border">
            {activity.map((a) => (
              <li
                key={a.id}
                className="flex items-center gap-3 px-4 py-2.5 text-[13px] text-foreground"
              >
                {a.text} <span className="ml-auto text-[11px] text-muted-foreground">{a.ago}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
      {tab === "repos" && (
        <Card className="p-4">
          <div className="flex items-center gap-2 rounded-md border border-border p-3">
            <Github size={16} className="text-muted-foreground" />
            <span className="text-[13px] font-medium text-foreground">
              devlink/{p.name.toLowerCase().replace(/\s+/g, "-")}
            </span>
            <span className="ml-auto text-[11px] text-muted-foreground">main · updated 2h ago</span>
          </div>
        </Card>
      )}
      {tab === "workspace" && <CollaborativeWorkspace projectId={projectId} />}
      {tab === "dashboard" && (
        <ProjectDashboard projectId={projectId} currentUserRole={currentUserRole} />
      )}
    </div>
  );
}
