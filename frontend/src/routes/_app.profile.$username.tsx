import { createFileRoute, notFound, Link, useNavigate } from "@tanstack/react-router";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { currentUser } from "@/mocks/seed";
import { toast } from "sonner";
import { useState, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { profileSummaryApi, type ProfileSummaryResponse } from "@/api";
import { usersApi } from "@/api/modules/users";
import { projectsApi, type ExtendedProject } from "@/api/modules/projects";
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
  FolderOpen,
  Plus,
  Award,
  FolderKanban,
  Users,
} from "lucide-react";
import { ReportUserModal } from "@/components/shared/ReportUserModal";
import { analyticsApi } from "@/api/modules/analytics";
import SkillsCard from "@/components/profile/SkillsCard";
import ExperienceCard from "@/components/profile/ExperienceCard";
import { ProfileViewersList } from "@/components/profile/ProfileViewersList";
import { PinnedProjectsCard } from "@/components/profile/PinnedProjectsCard";
import { ProfileCompletionChecklist } from "@/components/profile/ProfileCompletionChecklist";
import { PortfolioExportDialog } from "@/components/profile/PortfolioExportDialog";
import { FollowButton } from "@/components/shared/FollowButton";
import { useFollowStatus } from "@/hooks/useFollow";
import { ActivityTimeline } from "@/components/profile/ActivityTimeline";
import { ContributionHeatmap } from "@/components/profile/ContributionHeatmap";
import { GitHubInsights } from "@/components/github/GitHubInsights";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";
import { CollaborationStatusBadge } from "@/features/collaboration/components/CollaborationStatusBadge";
import { CollaborationStatusPicker } from "@/features/collaboration/components/CollaborationStatusPicker";
import { useCollaborationStatus } from "@/hooks/useCollaborationStatus";
import { EditProfileModal } from "@/components/profile/EditProfileModal";
import { ManageSkillsModal } from "@/components/profile/ManageSkillsModal";
import DonationModal from "@/components/profile/DonationModal";
import { Heart } from "lucide-react";

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

function ProfilePage() {
  const { username } = Route.useParams();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const navigate = useNavigate();

  // Fetch real user profile from backend
  const {
    data: fetchedUser,
    isLoading: isUserLoading,
    isError: isUserError,
  } = useQuery({
    queryKey: ["profile", username],
    queryFn: async () => {
      try {
        const res = await usersApi.getByUsername(username);
        return res;
      } catch (err) {
        // Fallback for currently logged in mock session user if offline
        if (username === currentUser.handle) {
          return {
            id: currentUser.id,
            username: currentUser.handle,
            first_name: currentUser.name.split(" ")[0] || currentUser.name,
            last_name: currentUser.name.split(" ").slice(1).join(" ") || "",
            bio: "Product engineer. Ships fast, sleeps sometimes.",
            role: "Full Stack Developer",
            profile_image: currentUser.avatar,
            premium: currentUser.premium,
            verified: currentUser.verified,
            skills: [],
          };
        }
        throw err;
      }
    },
  });

  const me =
    username === currentUser.handle ||
    Boolean(fetchedUser && fetchedUser.username === currentUser.handle);
  const profileAction = (
    <Link
      to="/settings"
      className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
    >
      Update profile
    </Link>
  );

  const b = useMemo(() => {
    if (!fetchedUser) return null;
    const name =
      fetchedUser.first_name && fetchedUser.last_name
        ? `${fetchedUser.first_name} ${fetchedUser.last_name}`
        : fetchedUser.first_name || fetchedUser.username || username;

    const rawSkills: string[] = Array.isArray(fetchedUser.skills) ? fetchedUser.skills : [];
    const profileSkills: ProfileSkill[] = rawSkills.map((skillName: string) => ({
      name: skillName,
      level: "Intermediate",
      category: "Languages",
    }));

    return {
      id: fetchedUser.id || "",
      name,
      firstName: fetchedUser.first_name || "",
      lastName: fetchedUser.last_name || "",
      handle: fetchedUser.username || username,
      avatar: fetchedUser.profile_image || "",
      headline: fetchedUser.headline ?? "",
      bio: fetchedUser.bio ?? "",
      location: fetchedUser.location ?? "",
      country: fetchedUser.location ?? "",
      website: fetchedUser.website ?? "",
      githubUrl: fetchedUser.github_url ?? "",
      linkedinUrl: fetchedUser.linkedinUrl ?? fetchedUser.linkedin_url ?? "",
      twitterUrl: fetchedUser.twitterUrl ?? fetchedUser.twitter_url ?? "",
      portfolioUrl: fetchedUser.portfolioUrl ?? fetchedUser.portfolio_url ?? "",
      role: fetchedUser.role ?? "Developer",
      company: fetchedUser.company ?? "",
      experienceLevel: fetchedUser.experience_level ?? "Intermediate",
      skills: rawSkills,
      profileSkills,
      experience: fetchedUser.experience ?? [],
      education: fetchedUser.education ?? [],
      badges: fetchedUser.badges ?? [],
      online: Boolean(fetchedUser.online || fetchedUser.is_active),
      premium: Boolean(fetchedUser.premium),
      verified: Boolean(fetchedUser.is_verified || fetchedUser.verified),
      collaborationStatus: fetchedUser.collaboration_status ?? "available",
      followers: fetchedUser.followers_count ?? 0,
      following: fetchedUser.following_count ?? 0,
      contributions: fetchedUser.contributions_count ?? 0,
    };
  }, [fetchedUser, username]);

  // Fetch real projects for this user
  const { data: userProjects = [], isLoading: isProjectsLoading } = useQuery({
    queryKey: ["user-projects", b?.id],
    queryFn: async () => {
      if (!b?.id) return [];
      try {
        const res = await projectsApi.byUser(b.id);
        return Array.isArray(res) ? res : [];
      } catch {
        return [];
      }
    },
    enabled: Boolean(b?.id),
  });

  const { data: followStatus } = useFollowStatus(b?.id || "");
  const followerCount = followStatus?.follower_count ?? b?.followers ?? 0;

  // Live collaboration presence status
  const {
    status: myStatus,
    setStatus: setMyStatus,
    isLoading: isStatusLoading,
  } = useCollaborationStatus();

  const [isDonationModalOpen, setIsDonationModalOpen] = useState(false);

  // Profile banner & avatar state
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [bannerUrl, setBannerUrl] = useState<string | null>(
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=400&fit=crop&auto=format",
  );
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(undefined);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isManageSkillsOpen, setIsManageSkillsOpen] = useState(false);

  // Profile summary state
  const [summary, setSummary] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSummary, setEditedSummary] = useState("");

  const summaryMutation = useMutation({
    mutationFn: () => profileSummaryApi.generate(b?.id || ""),
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

  // 1. Loading state
  if (isUserLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        {/* Banner & Avatar Skeleton */}
        <Card className="overflow-hidden p-0 border-border">
          <Skeleton className="h-44 w-full" />
          <div className="p-6 pt-0">
            <div className="flex flex-wrap items-start gap-5 -mt-12">
              <Skeleton className="h-24 w-24 rounded-full ring-4 ring-card" />
              <div className="min-w-0 flex-1 pt-12 sm:pt-4 space-y-3">
                <Skeleton className="h-7 w-48" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex gap-4 pt-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
              <div className="flex gap-2 pt-12 sm:pt-4">
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-9 w-24" />
              </div>
            </div>
          </div>
        </Card>

        <div className="grid gap-4 lg:grid-cols-3 items-start">
          <div className="space-y-4">
            <Skeleton className="h-48 w-full rounded-lg" />
            <Skeleton className="h-48 w-full rounded-lg" />
          </div>
          <div className="space-y-4 lg:col-span-2">
            <Skeleton className="h-64 w-full rounded-lg" />
            <Skeleton className="h-48 w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  // 2. Error / Not found state
  if (isUserError || !b) {
    return (
      <Card className="p-12 text-center space-y-4">
        <AlertTriangle className="mx-auto h-12 w-12 text-destructive/80" />
        <TypoHeading as="h2" className="text-xl">
          User Profile Not Found
        </TypoHeading>
        <TypoCaption as="p">
          We couldn't find a DevLink profile for @{username}. The user might not exist or the
          profile is private.
        </TypoCaption>
        <div className="pt-2">
          <Link
            to="/builders"
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90"
          >
            Explore Developers
          </Link>
        </div>
      </Card>
    );
  }

  const currentAvatar = avatarUrl ?? b.avatar;

  return (
    <div className="space-y-4">
      {me ? (
        <Card className="p-6 bg-gradient-to-r from-primary-soft via-transparent to-transparent border-primary/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <TypoSection>
                <span className="text-lg">🚀</span> Your Shareable Public Portfolio
              </TypoSection>
              <TypoCaption as="p">
                Showcase your projects, skills, and flares with beautiful custom themes, custom
                layouts, and a direct contact form.
              </TypoCaption>
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
                className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors cursor-pointer"
              >
                Copy Link
              </button>
              <button
                onClick={() => setIsExportModalOpen(true)}
                className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
              >
                Export Profile
              </button>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-4 bg-muted/40">
          <div className="flex items-center justify-between gap-4">
            <TypoCaption as="p">
              Looking for a more polished, professional view of {b.name}'s work?
            </TypoCaption>
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
            avatar: currentAvatar,
            banner: bannerUrl || undefined,
            bio: b.bio,
            skills: b.skills,
            experience: b.experienceLevel || b.role || b.company,
            education: b.headline,
            githubUrl: b.githubUrl,
            portfolioUrl: b.portfolioUrl,
            projects: userProjects.length,
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
              src={currentAvatar}
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
              <TypoHeading as="h1">
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
              </TypoHeading>
              <TypoCaption as="p">
                @{b.handle} {b.role ? `· ${b.role}` : ""}
              </TypoCaption>
              <div className="mt-2 flex items-center gap-2">
                {me ? (
                  <CollaborationStatusPicker
                    value={myStatus ?? "available"}
                    onChange={(status) => setMyStatus(status)}
                    disabled={isStatusLoading}
                  />
                ) : (
                  <CollaborationStatusBadge status={b.collaborationStatus} />
                )}
              </div>
              {b.bio && <p className="mt-2 text-[13px] text-foreground">{b.bio}</p>}
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
                <div>
                  <span className="font-semibold">
                    {followStatus?.follower_count ?? b.followers ?? 0}
                  </span>{" "}
                  <TypoCaption>Followers</TypoCaption>
                </div>
                <div>
                  <span className="font-semibold">
                    {followStatus?.following_count ?? b.following ?? 0}
                  </span>{" "}
                  <TypoCaption>Following</TypoCaption>
                </div>
                <div>
                  <span className="font-semibold">{b.contributions ?? 0}</span>{" "}
                  <TypoCaption>Contributions</TypoCaption>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-muted-foreground">
                {b.country && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin size={12} /> {b.country}
                  </span>
                )}
                <span className="inline-flex items-center gap-1">
                  <Calendar size={12} /> Joined DevLink
                </span>
                {b.website && (
                  <a
                    href={b.website.startsWith("http") ? b.website : `https://${b.website}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 hover:text-primary transition-colors"
                  >
                    <LinkIcon size={12} /> {b.website.replace(/^https?:\/\//, "")}
                  </a>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {!me && <FollowButton userId={b.id} />}
              {!me && (
                <button
                  type="button"
                  onClick={() => setIsDonationModalOpen(true)}
                  className="inline-flex items-center gap-2 rounded-md bg-pink-600 px-3 py-2 text-[13px] font-semibold text-white transition-opacity hover:bg-pink-700"
                >
                  <Heart className="w-4 h-4" />
                  Sponsor
                </button>
              )}
              {!me && (
                <button
                  type="button"
                  onClick={() =>
                    navigate({
                      to: "/messages/$conversationId",
                      params: { conversationId: b.id },
                    })
                  }
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 cursor-pointer"
                >
                  <MessageCircle size={16} />
                  Contact Developer
                </button>
              )}
              {me && (
                <>
                  <button
                    type="button"
                    onClick={() => setIsEditProfileOpen(true)}
                    className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 cursor-pointer"
                  >
                    <Pencil size={16} />
                    Edit Profile
                  </button>

                  <Link
                    to="/profile-analytics"
                    className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted transition-colors"
                  >
                    <TrendingUp size={16} />
                    Analytics
                  </Link>
                </>
              )}
              <button
                type="button"
                onClick={() => {
                  const url = `${window.location.origin}/profile/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Profile link copied to clipboard!");
                }}
                className="inline-flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-[13px] font-medium text-foreground hover:bg-muted transition-colors cursor-pointer"
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
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground cursor-pointer"
              >
                <Pencil size={12} /> Edit
              </button>
              <button
                onClick={() => summaryMutation.mutate()}
                disabled={summaryMutation.isPending}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground disabled:opacity-50 cursor-pointer"
              >
                <RotateCw size={12} className={summaryMutation.isPending ? "animate-spin" : ""} />{" "}
                Regenerate
              </button>
            </div>
          )}
          {!summary && !summaryMutation.isPending && (
            <button
              onClick={() => summaryMutation.mutate()}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90 cursor-pointer"
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
                      className="rounded-md px-3 py-1.5 text-[11px] text-muted-foreground hover:bg-muted/50 cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      className="rounded-md bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground hover:opacity-90 cursor-pointer"
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
              <div className="mt-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    navigate({
                      to: "/messages/$conversationId",
                      params: { conversationId: b.id },
                    })
                  }
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 cursor-pointer"
                >
                  <MessageCircle size={16} />
                  Contact Developer
                </button>
                <button
                  onClick={() => setIsReportModalOpen(true)}
                  className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-[13px] font-semibold text-destructive hover:bg-destructive/20 transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <AlertTriangle size={14} /> Report
                </button>
              </div>
            )}
          </div>
        )}

        {!summary && !summaryMutation.isPending && !summaryMutation.isError && (
          <TypoCaption as="p">
            Generate an AI-powered professional summary based on your profile, skills, and activity.
          </TypoCaption>
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
          <SkillsCard
            skills={b.profileSkills ?? []}
            isOwnProfile={me}
            onManageSkills={me ? () => setIsManageSkillsOpen(true) : undefined}
            emptyAction={me ? profileAction : undefined}
          />
          <ExperienceCard
            role={b.role}
            company={b.company}
            experienceLevel={b.experienceLevel}
            entries={b.experience}
            emptyAction={me ? profileAction : undefined}
          />

          <PinnedProjectsCard username={b.handle} isOwnProfile={me} />

          <Card className="p-4">
            <p className="text-[13px] font-semibold text-foreground">Achievements</p>
            {b.badges && b.badges.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {b.badges.map((badge: string) => (
                  <span
                    key={badge}
                    className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary"
                  >
                    <span className="text-[14px]">🏅</span> {badge}
                  </span>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={Award}
                title="Achievements await"
                desc="Complete projects and contribute to the community to earn badges."
                action={
                  me ? (
                    <Link
                      to="/projects"
                      className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                    >
                      Explore projects
                    </Link>
                  ) : undefined
                }
                className="py-8"
              />
            )}
          </Card>

          {followerCount === 0 ? (
            <Card className="p-4">
              <p className="text-[13px] font-semibold text-foreground">Followers</p>
              <EmptyState
                icon={Users}
                title="Build your network"
                desc="Share your profile and collaborate with other builders to grow your audience."
                action={
                  me ? (
                    <Link
                      to="/builders"
                      className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                    >
                      Find builders
                    </Link>
                  ) : undefined
                }
                className="py-8"
              />
            </Card>
          ) : null}
        </div>

        <div className="flex flex-col gap-4 lg:col-span-2">
          {/* Projects Section */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div>
                <TypoHeading as="h2" className="text-sm font-semibold text-foreground">
                  Projects
                </TypoHeading>
                <TypoCaption as="p">
                  {me ? "Projects you have published" : `Projects built by ${b.name}`}
                </TypoCaption>
              </div>
              {me && (
                <Link
                  to="/projects"
                  className="inline-flex items-center gap-1 rounded-md bg-primary/10 hover:bg-primary/20 text-primary px-2.5 py-1 text-xs font-medium transition-colors"
                >
                  <Plus size={12} /> New Project
                </Link>
              )}
            </div>

            {isProjectsLoading ? (
              <div className="mt-3 space-y-2">
                <Skeleton className="h-12 w-full rounded-md" />
                <Skeleton className="h-12 w-full rounded-md" />
              </div>
            ) : userProjects.length === 0 ? (
              <div className="py-8 text-center">
                <FolderOpen className="mx-auto h-8 w-8 text-muted-foreground/60 mb-2" />
                <p className="text-sm font-medium text-foreground">No projects shared yet</p>
                <TypoCaption as="p" className="mt-1">
                  {me
                    ? "Showcase your work by creating your first project."
                    : `${b.name} hasn't published any public projects yet.`}
                </TypoCaption>
                {me && (
                  <Link
                    to="/projects"
                    className="inline-flex items-center gap-2 mt-4 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
                  >
                    <Plus size={14} /> Create Project
                  </Link>
                )}
              </div>
            ) : (
              <ul className="mt-3 divide-y divide-border">
                {userProjects.map((p: ExtendedProject) => (
                  <li key={p.id} className="py-2.5">
                    <Link
                      to="/projects/$projectId"
                      params={{ projectId: p.id }}
                      onClick={() => {
                        if (b.id) {
                          analyticsApi.trackClick("project", b.id, p.id).catch(() => {});
                        }
                      }}
                      className="flex items-center gap-3 hover:bg-muted/50 p-2 rounded-lg transition-colors w-full text-left"
                    >
                      <div className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary font-bold text-sm shrink-0">
                        {p.title ? p.title.charAt(0).toUpperCase() : "P"}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[13px] font-semibold text-foreground hover:text-primary transition-colors">
                          {p.title || (p as any).name}
                        </p>
                        <TypoCaption as="p" className="truncate">
                          {p.tagline ||
                            p.description ||
                            (Array.isArray((p as any).tech_stack)
                              ? (p as any).tech_stack.join(" · ")
                              : Array.isArray((p as any).stack)
                                ? (p as any).stack.join(" · ")
                                : "")}
                        </TypoCaption>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {(() => {
            const githubUrl = b.githubUrl;
            let githubUsername = undefined;
            if (githubUrl) {
              try {
                const url = new URL(githubUrl);
                githubUsername = url.pathname.split("/").filter(Boolean).pop();
              } catch (e) {
                // Ignore invalid URLs
              }
            }

            if (githubUsername) {
              return (
                <div className="mt-4">
                  <GitHubInsights username={githubUsername} />
                </div>
              );
            }
            return <ContributionHeatmap username={b.handle} className="mt-4" />;
          })()}
          <ActivityTimeline userId={b.id} emptyAction={me ? profileAction : undefined} />
        </div>
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

      {me && <PortfolioExportDialog open={isExportModalOpen} onOpenChange={setIsExportModalOpen} />}

      {me && (
        <EditProfileModal
          open={isEditProfileOpen}
          onOpenChange={setIsEditProfileOpen}
          initialData={{
            firstName: b.firstName,
            lastName: b.lastName,
            username: b.handle,
            headline: b.headline,
            bio: b.bio,
            location: b.location,
            website: b.website,
            profileImage: currentAvatar,
            githubUrl: b.githubUrl,
            linkedinUrl: b.linkedinUrl,
            twitterUrl: b.twitterUrl,
            portfolioUrl: b.portfolioUrl,
            role: b.role,
            experienceLevel: b.experienceLevel,
            company: b.company,
            skills: b.skills,
          }}
          onSuccess={(updated) => {
            if (updated && updated.username && updated.username !== b.handle) {
              navigate({ to: "/profile/$username", params: { username: updated.username } });
            }
          }}
        />
      )}

      {me && (
        <ManageSkillsModal
          open={isManageSkillsOpen}
          onOpenChange={setIsManageSkillsOpen}
          initialSkills={b.profileSkills}
          username={b.handle}
        />
      )}

      {!me && b.id && (
        <DonationModal
          isOpen={isDonationModalOpen}
          onClose={() => setIsDonationModalOpen(false)}
          recipientId={b.id}
          recipientName={b.name}
        />
      )}
    </div>
  );
}
