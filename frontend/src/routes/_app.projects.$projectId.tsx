import { createFileRoute, Link, notFound, Outlet } from "@tanstack/react-router";
import { useQuery, useMutation } from "@tanstack/react-query";
import { projectsService } from "@/services";
import { Card, TagChip, Avatar, Skeleton } from "@/components/shared/primitives";
import { api } from "@/api";
import { ProjectDashboard } from "@/features/projects/components/ProjectDashboard";
import { ProjectCalendar } from "@/features/projects/components/ProjectCalendar";
import { CollaborativeWorkspace } from "@/components/projects/CollaborativeWorkspace";
import { ProjectMembersList } from "@/features/projects/components/ProjectMembersList";
import { CloneProjectDialog } from "@/components/projects/CloneProjectDialog";
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
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { getMyApplications } from "@/lib/api";
import { useWithdrawApplication } from "@/hooks/useApplications";
import { ApplyModal } from "@/features/projects/components/ApplyModal";

import {
  ProjectMediaGallery,
  type ProjectMediaItem,
} from "@/components/project/ProjectMediaGallery";
import { ProjectMediaUploader } from "@/components/project/ProjectMediaUploader";

export const Route = createFileRoute("/_app/projects/$projectId")({
  loader: async ({ params }) => {
    const project = await projectsService.get(params.projectId).catch(() => null);
    if (!project) throw notFound();
    return { project };
  },
  head: ({ loaderData, params }) => {
    const p = loaderData?.project;
    return {
      meta: [
        { title: `${p ? p.name : params.projectId} — DevLink` },
        {
          name: "description",
          content: p?.description || "Project details, members, activity and repositories.",
        },
        { property: "og:title", content: `${p ? p.name : params.projectId} | DevLink Project` },
        {
          property: "og:description",
          content: p?.description || "Check out this project on DevLink.",
        },
        { property: "og:type", content: "website" },
        { name: "twitter:card", content: "summary_large_image" },
        { name: "twitter:title", content: `${p ? p.name : params.projectId} | DevLink Project` },
        {
          name: "twitter:description",
          content: p?.description || "Check out this project on DevLink.",
        },
      ],
    };
  },
  component: ProjectDetail,
});

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const loaderData = Route.useLoaderData();
  const { data: p, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsService.get(projectId),
    initialData: loaderData?.project,
  });
  const [tab, setTab] = useState<
    "overview" | "workspace" | "members" | "activity" | "repos" | "dashboard" | "calendar"
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

  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [isCloneDialogOpen, setIsCloneDialogOpen] = useState(false);
  const { data: myApps } = useQuery({
    queryKey: ["myApplications"],
    queryFn: getMyApplications,
  });
  const projectApplication = myApps?.find((a) => a.project_id === projectId);
  const withdrawMutation = useWithdrawApplication();

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

  // Media Gallery & Showcase state
  const [isMediaUploaderOpen, setIsMediaUploaderOpen] = useState(false);
  const [coverImage, setCoverImage] = useState(
    "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&auto=format&fit=crop&q=80",
  );
  const [videoDemoUrl, setVideoDemoUrl] = useState("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
  const [screenshots, setScreenshots] = useState<ProjectMediaItem[]>([
    {
      id: "demo-screen-1",
      url: "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&auto=format&fit=crop&q=80",
      type: "image",
      title: "Interactive Dashboard View",
      caption: "Real-time metrics and collaboration dashboard",
      order: 0,
    },
    {
      id: "demo-screen-2",
      url: "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=800&auto=format&fit=crop&q=80",
      type: "image",
      title: "Code Analytics & Pull Requests",
      caption: "Automated git metrics and contribution insights",
      order: 1,
    },
    {
      id: "demo-screen-3",
      url: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
      type: "image",
      title: "Settings & Team Permissions",
      caption: "Granular RBAC and project environment controls",
      order: 2,
    },
  ]);

  const handleSaveMedia = (data: {
    coverImage: string;
    screenshots: ProjectMediaItem[];
    videoDemoUrl: string;
  }) => {
    setCoverImage(data.coverImage);
    setScreenshots(data.screenshots);
    setVideoDemoUrl(data.videoDemoUrl);
  };

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

  if (isLoading) {
    return (
      <div className="space-y-4">
        <BackButton to="/projects" label="Back to projects" />

        {/* Header Card Skeleton */}
        <Card className="p-5">
          <div className="flex items-start gap-4">
            <Skeleton className="h-14 w-14 shrink-0 rounded-md animate-pulse" />
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-6 w-1/3 animate-pulse" />
              <Skeleton className="h-4 w-2/3 animate-pulse" />
              <div className="mt-3 flex gap-1.5">
                <Skeleton className="h-5 w-16 rounded-full animate-pulse" />
                <Skeleton className="h-5 w-20 rounded-full animate-pulse" />
                <Skeleton className="h-5 w-14 rounded-full animate-pulse" />
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <Skeleton className="h-8 w-24 rounded-md animate-pulse" />
              <Skeleton className="h-8 w-8 rounded-md animate-pulse" />
              <Skeleton className="h-8 w-8 rounded-md animate-pulse" />
              <div className="hidden gap-4 sm:flex">
                <Skeleton className="h-4 w-10 animate-pulse" />
                <Skeleton className="h-4 w-10 animate-pulse" />
                <Skeleton className="h-4 w-10 animate-pulse" />
              </div>
            </div>
          </div>
        </Card>

        {/* Tabs Row Skeleton */}
        <div className="flex items-center gap-1 border-b border-border pb-px">
          <Skeleton className="h-8 w-20 rounded-t-md animate-pulse" />
          <Skeleton className="h-8 w-24 rounded-t-md animate-pulse" />
          <Skeleton className="h-8 w-20 rounded-t-md animate-pulse" />
          <Skeleton className="h-8 w-20 rounded-t-md animate-pulse" />
          <Skeleton className="h-8 w-16 rounded-t-md animate-pulse" />
        </div>

        {/* Tab Content Area Skeleton */}
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8 space-y-4">
            <Card className="p-5 space-y-3">
              <Skeleton className="h-5 w-32 animate-pulse" />
              <Skeleton className="h-4 w-full animate-pulse" />
              <Skeleton className="h-4 w-full animate-pulse" />
              <Skeleton className="h-4 w-3/4 animate-pulse" />
            </Card>
          </div>
          <div className="lg:col-span-4 space-y-4">
            <Card className="p-5 space-y-3">
              <Skeleton className="h-5 w-28 animate-pulse" />
              <Skeleton className="h-10 w-full animate-pulse" />
              <Skeleton className="h-10 w-full animate-pulse" />
            </Card>
          </div>
        </div>
      </div>
    );
  }
  if (!p) {
    // When a child sub-route (e.g. collaboration-metrics) is active and the
    // project data is unavailable (backend offline / not found), render the
    // child outlet so sub-pages can display their own standalone content
    // instead of crashing the whole route tree.
    return <Outlet />;
  }

  const tabs = dashboard
    ? (["overview", "workspace", "members", "activity", "repos", "dashboard", "calendar"] as const)
    : (["overview", "workspace", "members", "activity", "repos", "calendar"] as const);

  return (
    <div className="space-y-4">
      <BackButton to="/projects" label="Back to projects" />
      <Card className="p-5">
        <div className="flex items-start gap-4">
          <span className="grid h-14 w-14 shrink-0 place-items-center rounded-md bg-muted text-3xl">
            {p.icon}
          </span>
          <div className="min-w-0 flex-1">
            <TypoHeading as="h1">{p.name}</TypoHeading>
            <TypoCaption as="p">{p.description}</TypoCaption>
            <div className="mt-3 flex flex-wrap gap-1">
              {p.stack.map((s: string) => (
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

            {!isOwner && projectApplication ? (
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-primary">
                  Status: {projectApplication.status}
                </span>
                <button
                  type="button"
                  onClick={() => withdrawMutation.mutate(projectApplication.id)}
                  disabled={withdrawMutation.isPending}
                  className="inline-flex items-center rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-[12px] font-medium text-destructive transition-colors hover:bg-destructive/20 disabled:opacity-50"
                >
                  Withdraw
                </button>
              </div>
            ) : !isOwner ? (
              <button
                type="button"
                onClick={() => setIsApplyModalOpen(true)}
                className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-[12px] font-medium text-primary-foreground transition-colors hover:opacity-90"
              >
                Apply
              </button>
            ) : null}

            <ShareProjectButton projectTitle={p.name} projectDescription={p.description} />

            <button
              type="button"
              onClick={() => setIsCloneDialogOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-muted"
              aria-label="Clone project template"
            >
              <Copy size={14} />
              Clone
            </button>

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
          <div className="space-y-4 lg:col-span-2">
            <ProjectMediaGallery
              coverImage={coverImage}
              screenshots={screenshots}
              videoDemoUrl={videoDemoUrl}
              isOwner={isOwner}
              onManageMedia={() => setIsMediaUploaderOpen(true)}
            />
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">About</p>
              <Markdown content={p.description} className="mt-2 text-muted-foreground" />
              <p className="mt-4 text-[13px] font-semibold text-foreground">Progress</p>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full bg-primary" style={{ width: `${p.progress}%` }} />
              </div>
              <TypoCaption as="p">{p.progress}% complete</TypoCaption>
            </Card>
          </div>
          <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">Owner</p>
            <TypoCaption as="p">{p.owner}</TypoCaption>
            <p className="mt-4 text-[13px] font-semibold text-foreground">Status</p>
            <TypoCaption as="p">{p.status}</TypoCaption>

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
                        <TypoCaption as="p">{selectedTags.length} tags selected</TypoCaption>
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
                {a.text} <TypoCaption>{a.ago}</TypoCaption>
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
            <TypoCaption>main · updated 2h ago</TypoCaption>
          </div>
        </Card>
      )}
      {tab === "workspace" && <CollaborativeWorkspace projectId={projectId} />}
      {tab === "dashboard" && (
        <ProjectDashboard projectId={projectId} currentUserRole={currentUserRole} />
      )}
      {tab === "calendar" && (
        <ProjectCalendar projectId={projectId} currentUserRole={currentUserRole} />
      )}

      <ApplyModal
        isOpen={isApplyModalOpen}
        onClose={() => setIsApplyModalOpen(false)}
        projectId={projectId}
      />

      <ProjectMediaUploader
        isOpen={isMediaUploaderOpen}
        onClose={() => setIsMediaUploaderOpen(false)}
        initialCoverImage={coverImage}
        initialScreenshots={screenshots}
        initialVideoDemoUrl={videoDemoUrl}
        onSave={handleSaveMedia}
      />

      {p && (
        <CloneProjectDialog
          project={{
            id: p.id,
            title: p.name,
            name: p.name,
            tagline: p.description,
            description: p.description,
            stage: "idea",
            stars: p.stars,
            views: p.views,
            forks: p.forks,
            members: p.members,
            icon: p.icon,
            stack: p.stack,
            ownerId: p.ownerId,
            tags: p.stack,
            owner: p.owner,
            progress: 0,
            status: "recruiting",
          }}
          open={isCloneDialogOpen}
          onOpenChange={setIsCloneDialogOpen}
        />
      )}
    </div>
  );
}
