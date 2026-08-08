import { createFileRoute, notFound, Link, useNavigate } from "@tanstack/react-router";
import { Card, TagChip, Avatar, Skeleton } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { builders, currentUser, projects, type Builder, type UserRole } from "@/mocks/seed";
import { toast } from "sonner";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { profileSummaryApi, type ProfileSummaryResponse } from "@/api";
import { cn } from "@/lib/utils";
import {
  MapPin,
  Calendar,
  Link as LinkIcon,
  MessageCircle,
  Mail,
  AlertTriangle,
  Sparkles,
  Pencil,
  RotateCw,
  BadgeCheck,
  Camera,
  TrendingUp,
} from "lucide-react";
import { copyText } from "@/lib/clipboard";
import { ReportUserModal } from "@/components/shared/ReportUserModal";
import { analyticsApi } from "@/api/modules/analytics";
import SkillsCard from "@/components/profile/SkillsCard";
import ExperienceCard from "@/components/profile/ExperienceCard";
import { ProfileViewersList } from "@/components/profile/ProfileViewersList";
import { ProfileCompletionChecklist } from "@/components/profile/ProfileCompletionChecklist";
import { FollowButton } from "@/components/shared/FollowButton";
import { useFollowStatus } from "@/hooks/useFollow";

export const Route = createFileRoute("/_app/profile/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username} — DevLink` },
      {
        name: "description",
        content: `${params.username}'s DevLink profile: skills, projects and activity.`,
      },
    ],
  }),
  component: ProfilePage,
});

type ProfileSkill = {
  name: string;
  level?: string;
  category?: string;
  yearsOfExperience?: number;
};

type ProfileFormValues = {
  headline: string;
  bio: string;
  location: string;
  timezone: string;
  website: string;
  resumeUrl: string;
  portfolioUrl: string;
  githubUrl: string;
  linkedinUrl: string;
  role: string;
  experienceLevel: string;
  company: string;
  profileSkills: ProfileSkill[];
  techStack: string[];
};

function mapBuilderToFormValues(builder: Builder): ProfileFormValues {
  return {
    headline: builder.headline ?? "",
    bio: builder.bio ?? "",
    location: builder.location ?? "",
    timezone: builder.timezone ?? "",
    website: builder.website ?? "",
    resumeUrl: builder.resumeUrl ?? "",
    portfolioUrl: builder.portfolioUrl ?? "",
    githubUrl: builder.githubUrl ?? "",
    linkedinUrl: builder.linkedinUrl ?? "",
    role: builder.role ?? "",
    experienceLevel: builder.experienceLevel ?? "",
    company: builder.company ?? "",
    profileSkills: builder.profileSkills?.length
      ? builder.profileSkills.map((skill: ProfileSkill) => ({
          ...skill,
          level: skill.level ?? "Intermediate",
          yearsOfExperience: skill.yearsOfExperience ?? 0,
        }))
      : builder.skills.map((skill: string) => ({
          name: skill,
          level: "Intermediate",
          category: "general",
        })),
    techStack: builder.techStack ?? [],
  };
}

function buildUpdatedBuilder(builder: Builder, values: ProfileFormValues): Builder {
  return {
    ...builder,
    headline: values.headline || undefined,
    bio: values.bio || "",
    location: values.location || undefined,
    timezone: values.timezone || undefined,
    website: values.website || undefined,
    resumeUrl: values.resumeUrl || undefined,
    portfolioUrl: values.portfolioUrl || undefined,
    githubUrl: values.githubUrl || undefined,
    linkedinUrl: values.linkedinUrl || undefined,
    role: (values.role as UserRole) || "Developer",
    experienceLevel: values.experienceLevel || undefined,
    company: values.company || undefined,
    profileSkills: values.profileSkills.map((skill) => ({
      name: skill.name,
      level: skill.level || "Intermediate",
      category: skill.category || "general",
      yearsOfExperience: skill.yearsOfExperience ?? 0,
    })),
    techStack: values.techStack.filter(Boolean),
    skills: values.profileSkills.map((skill) => skill.name),
  };
}

function ProfilePage() {
  const { username } = Route.useParams();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const navigate = useNavigate();
  const me = username === currentUser.handle;
  const b = me
    ? {
        ...builders[0],
        name: currentUser.name,
        handle: currentUser.handle,
        avatar: currentUser.avatar,
        bio: "Product engineer. Ships fast, sleeps sometimes.",
        role: "Full Stack Developer",
        id: currentUser.id,
      }
    : builders.find((x) => x.handle === username);
  if (!b) throw notFound();

  const { data: followStatus } = useFollowStatus(b.id);

  // Profile banner & avatar state
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [bannerUrl, setBannerUrl] = useState<string | null>(
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=400&fit=crop&auto=format",
  );
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(b.avatar);

  // Profile summary state
  const [summary, setSummary] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSummary, setEditedSummary] = useState("");

  const summaryMutation = useMutation({
    mutationFn: () => profileSummaryApi.generate(b.id),
    onSuccess: (data: ProfileSummaryResponse) => {
      setSummary(data.summary);
      setEditedSummary(data.summary);
      toast.success("Profile summary generated!");
    },
    onError: () => {
      toast.error("Failed to generate summary. Please try again.");
    },
  });

  const handleEdit = () => {
    setEditedSummary(summary || "");
    setIsEditing(true);
  };

  const handleSave = () => {
    setSummary(editedSummary);
    setIsEditing(false);
    toast.success("Summary updated!");
  };

  const handleCancel = () => {
    setEditedSummary(summary || "");
    setIsEditing(false);
  };

  return (
    <div className="space-y-4">
      {me ? (
        <Card className="p-6 bg-gradient-to-r from-primary-soft via-transparent to-transparent border-primary/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <span className="text-lg">🚀</span> Your Shareable Public Portfolio
              </h3>
              <p className="text-xs text-muted-foreground">
                Showcase your projects, skills, and flares with beautiful custom themes, custom
                layouts, and a direct contact form.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                to="/portfolio/$username"
                params={{ username: b.handle }}
                className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                View Portfolio
              </Link>
              <button
                onClick={() => {
                  const url = `${window.location.origin}/portfolio/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Portfolio link copied to clipboard!");
                }}
                className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
              >
                Copy Link
              </button>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-4 bg-muted/40">
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              Looking for a more polished, professional view of {b.name}'s work?
            </p>
            <Link
              to="/portfolio/$username"
              params={{ username: b.handle }}
              className="inline-flex items-center justify-center rounded-md border border-primary text-primary hover:bg-primary-soft px-3 py-1.5 text-xs font-semibold transition-colors"
            >
              View Public Portfolio
            </Link>
          </div>
        </Card>
      )}

      {me && (
        <ProfileCompletionChecklist
          userProfile={{
            avatar: avatarUrl,
            banner: bannerUrl || undefined,
            bio: b.bio,
            skills: b.profileSkills?.map((s) => s.name) ?? b.skills,
            experience: b.experienceLevel || b.role || b.company,
            education: b.headline,
            githubUrl: b.githubUrl,
            portfolioUrl: b.portfolioUrl,
            projects: projects.length,
          }}
        />
      )}

      {/* Profile Card with Cover Banner & Avatar */}
      <Card
        className={cn(
          "overflow-hidden p-0",
          b.premium && "border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.08)]",
        )}
      >
        {/* Cover Banner */}
        <div className="group relative h-44 w-full overflow-hidden bg-muted">
          {bannerUrl ? (
            <img src={bannerUrl} alt="Profile banner" className="h-full w-full object-cover" />
          ) : (
            <div
              className={cn(
                "h-full w-full bg-gradient-to-r",
                b.premium
                  ? "from-amber-600/40 via-amber-500/20 to-purple-600/30"
                  : "from-primary/30 to-purple-500/30",
              )}
            />
          )}

          {me && (
            <button
              type="button"
              onClick={() => setIsBannerModalOpen(true)}
              className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-md bg-black/60 px-3 py-1.5 text-xs font-medium text-white backdrop-blur-sm transition-all hover:bg-black/80 cursor-pointer"
            >
              <Camera size={14} />
              Edit cover banner
            </button>
          )}
        </div>

        <div className="p-6 pt-0">
          <div className="flex flex-wrap items-start gap-5 -mt-12">
            <UserAvatar
              src={avatarUrl}
              name={b.name}
              size="2xl"
              status={b.online}
              verified={b.verified}
              premium={b.premium}
              editable={me}
              onImageUpload={(url) => {
                setAvatarUrl(url);
                toast.success("Avatar updated!");
              }}
              className="ring-4 ring-card shadow-lg"
            />
            <div className="min-w-0 flex-1 pt-12 sm:pt-4">
              <h1 className="text-[22px] font-bold text-foreground flex items-center gap-2">
                {b.name}
                {b.verified &&
                  (b.premium ? (
                    <span className="inline-flex items-center gap-1.5">
                      <BadgeCheck
                        className="text-amber-500 fill-amber-500/10 h-6 w-6 animate-pulse"
                        aria-label="Premium Verified User"
                      />
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 border border-amber-500/30 text-amber-500 px-2 py-0.5 rounded-full shadow-[0_0_8px_rgba(245,158,11,0.2)] animate-pulse">
                        PRO VERIFIED
                      </span>
                    </span>
                  ) : (
                    <BadgeCheck className="text-primary h-6 w-6" aria-label="Verified User" />
                  ))}
              </h1>
              <p className="text-[13px] text-muted-foreground">
                @{b.handle} · {b.role}
              </p>
              <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
                <div>
                  <span className="font-semibold">
                    {followStatus?.follower_count ?? b.followers ?? 0}
                  </span>
                  <span className="m-1 text-muted-foreground">Followers</span>
                </div>
                <div>
                  <span className="font-semibold">
                    {followStatus?.following_count ?? b.following ?? 0}
                  </span>
                  <span className="m-1 text-muted-foreground">Following</span>
                </div>
                <div>
                  <span className="font-semibold">{b.contributions ?? 0}</span>
                  <span className="ml-1 text-muted-foreground">Contributions</span>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <MapPin size={12} /> {b.country}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Calendar size={12} /> Joined 2024
                </span>
                <span className="inline-flex items-center gap-1">
                  <LinkIcon size={12} /> devlink.io/{b.handle}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {!me && <FollowButton userId={b.id} />}
              {!me && (
                <button
                  type="button"
                  onClick={() =>
                    navigate({
                      to: "/messages/$conversationId",
                      params: { conversationId: b.id },
                    })
                  }
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  <MessageCircle size={16} />
                  Contact Developer
                </button>
              )}
              {me && (
                <Link
                  to="/profile-analytics"
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  <TrendingUp size={16} />
                  Profile Analytics
                </Link>
              )}
              <button
                type="button"
                onClick={() => {
                  const url = `${window.location.origin}/profile/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Profile link copied to clipboard!");
                }}
                className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted transition-colors"
              >
                <LinkIcon size={16} />
                Copy Link
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* AI Profile Summary Section */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[13px] font-semibold text-foreground flex items-center gap-2">
            <Sparkles size={14} className="text-primary" />
            AI Profile Summary
          </p>
          {summary && !isEditing && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleEdit}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              >
                <Pencil size={12} /> Edit
              </button>
              <button
                onClick={() => summaryMutation.mutate()}
                disabled={summaryMutation.isPending}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground disabled:opacity-50"
              >
                <RotateCw size={12} className={summaryMutation.isPending ? "animate-spin" : ""} />{" "}
                Regenerate
              </button>
            </div>
          )}
          {!summary && !summaryMutation.isPending && (
            <button
              onClick={() => summaryMutation.mutate()}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90"
            >
              <Sparkles size={12} /> Generate Summary
            </button>
          )}
        </div>

        {summaryMutation.isPending && (
          <div className="mt-3 space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}

        {summary && !summaryMutation.isPending && (
          <div className="mt-3">
            {isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  maxLength={500}
                  rows={4}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 resize-none"
                />
                <div className="flex items-center justify-between">
                  <p
                    className={cn(
                      "text-[11px]",
                      editedSummary.length > 450 ? "text-orange-500" : "text-muted-foreground",
                    )}
                  >
                    {editedSummary.length}/500 characters
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCancel}
                      className="rounded-md px-3 py-1.5 text-[11px] text-muted-foreground hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      className="rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-[13px] text-foreground leading-relaxed">{summary}</p>
            )}
            {!me && (
              <>
                <button
                  type="button"
                  onClick={() =>
                    navigate({
                      to: "/messages/$conversationId",
                      params: { conversationId: b.id },
                    })
                  }
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  <MessageCircle size={16} />
                  Contact Developer
                </button>
                <button
                  onClick={() => setIsReportModalOpen(true)}
                  className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-[13px] font-semibold text-destructive hover:bg-destructive/20 transition-colors flex items-center gap-1"
                >
                  <AlertTriangle size={14} /> Report
                </button>
              </>
            )}
          </div>
        )}

        {!summary && !summaryMutation.isPending && !summaryMutation.isError && (
          <p className="mt-2 text-[12px] text-muted-foreground">
            Generate an AI-powered professional summary based on your profile, skills, and activity.
          </p>
        )}

        {summaryMutation.isError && (
          <p className="mt-2 text-[12px] text-destructive">
            Failed to generate summary. Please try again.
          </p>
        )}
      </Card>

      {me && <ProfileViewersList className="mt-4" />}

      <div className="grid gap-4 lg:grid-cols-3 items-start">
        <div className="flex flex-col gap-4">
          {/* <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">Skills</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {b.skills.map((s) => (
                <TagChip key={s}>{s}</TagChip>
              ))}
            </div>
          </Card> */}
          <SkillsCard skills={b.profileSkills ?? []} />
          <ExperienceCard role={b.role} company={b.company} experienceLevel={b.experienceLevel} />

          {b.pinnedProjects?.length ? (
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Pinned Projects</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {b.pinnedProjects.map((project) => (
                  <TagChip key={project}>{project}</TagChip>
                ))}
              </div>
            </Card>
          ) : null}

          {b.badges && b.badges.length > 0 && (
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Badges</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {b.badges.map((badge) => (
                  <span
                    key={badge}
                    className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary"
                  >
                    <span className="text-[14px]">🏅</span> {badge}
                  </span>
                ))}
              </div>
            </Card>
          )}
        </div>

        <Card className="p-4 lg:col-span-2">
          <p className="text-[13px] font-semibold text-foreground">Projects</p>
          <ul className="mt-3 divide-y divide-border">
            {projects.slice(0, 4).map((p) => (
              <li key={p.id} className="py-2">
                <Link
                  to="/projects/$projectId"
                  params={{ projectId: p.id }}
                  onClick={() => {
                    if (b.id) {
                      analyticsApi.trackClick("project", b.id, p.id).catch(() => {});
                    }
                  }}
                  className="flex items-center gap-3 hover:bg-muted/50 p-1.5 rounded-lg transition-colors w-full text-left"
                >
                  <span className="grid h-8 w-8 place-items-center rounded-md bg-muted text-lg shrink-0">
                    {p.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-semibold text-foreground hover:text-primary transition-colors">
                      {p.name}
                    </p>
                    <p className="truncate text-[11px] text-muted-foreground">
                      {p.stack.join(" · ")}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      {!me && (
        <ReportUserModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          userId={b.id || ""}
          username={b.handle}
        />
      )}

      {me && (
        <ImageCropUploadModal
          isOpen={isBannerModalOpen}
          onClose={() => setIsBannerModalOpen(false)}
          onUploadSuccess={(url) => {
            setBannerUrl(url);
            toast.success("Cover banner updated!");
          }}
          mode="banner"
          title="Upload Cover Banner"
        />
      )}
    </div>
  );
}
