import { createFileRoute, notFound, Link, useNavigate } from "@tanstack/react-router";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { currentUser, builders, projects } from "@/mocks/seed";
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
  Globe,
  Briefcase,
  GraduationCap,
  FolderGit2,
  ExternalLink,
  Heart,
} from "lucide-react";
import { ReportUserModal } from "@/components/shared/ReportUserModal";
import { analyticsApi } from "@/api/modules/analytics";
import SkillsCard from "@/components/profile/SkillsCard";
import ExperienceCard from "@/components/profile/ExperienceCard";
import EducationCard from "@/components/profile/EducationCard";
import CertificationsCard from "@/components/profile/CertificationsCard";
import FeaturedRepositoriesCard from "@/components/profile/FeaturedRepositoriesCard";
import PortfolioShowcaseCard from "@/components/profile/PortfolioShowcaseCard";
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
import { ReputationTrustCard } from "@/components/reputation/ReputationTrustCard";
import { TrustScoreBadge } from "@/components/reputation/TrustScoreBadge";
import { reputationApi } from "@/api/modules/reputation";
import { FollowersListModal } from "@/components/shared/FollowersListModal";
import DonationModal from "@/components/profile/DonationModal";

export const Route = createFileRoute("/_app/profile/$username")({
  head: ({ params }) => ({
    meta: [
      { title: `@${params.username} — DevLink` },
      {
        name: "description",
        content: `${params.username}'s DevLink profile: skills, projects, experience and professional background.`,
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

export function ProfilePage() {
  const { username } = Route.useParams();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const navigate = useNavigate();
  const me = username === currentUser.handle;
  const b = me
    ? {
        ...builders[0],
        name: currentUser.name,
        firstName: "Alex",
        lastName: "Chen",
        handle: currentUser.handle,
        avatar: currentUser.avatar,
        bio: "Product engineer & open source maintainer. Ships fast, builds scalable systems.",
        role: "Senior Full Stack Engineer",
        headline: "Senior Full Stack Engineer • Open Source Enthusiast • React & FastAPI",
        location: "San Francisco, CA",
        website: "https://devlink.io/alex",
        openToWork: true,
        availability: "Immediate (Full-time & Remote)",
        id: currentUser.id,
        premium: currentUser.premium,
        verified: currentUser.verified,
        experienceEntries: [
          {
            title: "Senior Full Stack Engineer",
            company: "DevLink Open Source",
            experienceLevel: "Senior",
            period: "2023 – Present",
            description: "Leading frontend architecture, real-time collaboration engines, and developer tooling.",
          },
          {
            title: "Software Engineer",
            company: "Acme Cloud Corp",
            experienceLevel: "Mid-level",
            period: "2021 – 2023",
            description: "Built distributed backend microservices in Go and Python.",
          },
        ],
        education: [
          {
            school: "University of California, Berkeley",
            degree: "B.S. in Computer Science",
            years: "2017 – 2021",
          },
        ],
        certifications: [
          {
            id: "cert_1",
            name: "AWS Certified Solutions Architect – Professional",
            issuer: "Amazon Web Services",
            issueDate: "2024",
            credentialId: "AWS-PSA-84920",
            credentialUrl: "https://aws.amazon.com/verification",
          },
          {
            id: "cert_2",
            name: "CKA: Certified Kubernetes Administrator",
            issuer: "Linux Foundation / CNCF",
            issueDate: "2023",
            credentialId: "LF-CKA-10294",
            credentialUrl: "https://cncf.io",
          },
        ],
        featuredRepositories: [
          {
            id: "repo_1",
            name: "devlink-core",
            description: "High-performance developer networking engine with real-time collaboration.",
            language: "TypeScript",
            stars: 1240,
            forks: 312,
            repoUrl: "https://github.com/devlink/devlink",
            liveUrl: "https://devlink.io",
            topics: ["react", "fastapi", "webrtc"],
          },
          {
            id: "repo_2",
            name: "fastapi-realtime-broker",
            description: "Lightweight WebSocket state synchronization broker for modern web applications.",
            language: "Python",
            stars: 580,
            forks: 94,
            repoUrl: "https://github.com/devlink/broker",
            topics: ["python", "asyncio", "redis"],
          },
        ],
        portfolio: [
          {
            id: "port_1",
            title: "DevLink Collaboration Platform",
            description: "Full-scale developer hub empowering builders to match, create hackathon teams, and showcase repositories.",
            link: "https://devlink.io",
            role: "Lead Architect",
            tags: ["Next.js", "FastAPI", "TailwindCSS"],
            year: "2026",
          },
          {
            id: "port_2",
            title: "AI Match scoring engine",
            description: "High-speed vector similarity matching algorithm for developer skill compatibility.",
            link: "https://devlink.io/matching",
            role: "Creator",
            tags: ["PyTorch", "Redis", "TypeScript"],
            year: "2025",
          },
        ],
      }
    : builders.find((x) => x.handle === username);

  if (!b) throw notFound();

  // Ensure default networking collections if not populated on mock builder
  const headline = (b as any).headline || `${b.role} • Building open source products`;
  const openToWork = (b as any).openToWork ?? true;
  const availability = (b as any).availability ?? "Immediate (Full-time & Remote)";
  const website = (b as any).website || `https://${b.handle}.dev`;
  const education = (b as any).education ?? [
    {
      school: "Stanford University",
      degree: "B.S. in Computer Science",
      years: "2018 – 2022",
    },
  ];
  const certifications = (b as any).certifications ?? [
    {
      id: "cert_def_1",
      name: "AWS Certified Developer – Associate",
      issuer: "Amazon Web Services",
      issueDate: "2024",
      credentialId: "AWS-DVA-93821",
      credentialUrl: "https://aws.amazon.com",
    },
  ];
  const featuredRepositories = (b as any).featuredRepositories ?? [
    {
      id: "repo_def_1",
      name: `${b.handle}-portfolio-starter`,
      description: "Modern developer portfolio template with customizable widgets and theme tokens.",
      language: "TypeScript",
      stars: 342,
      forks: 88,
      repoUrl: "https://github.com",
      topics: ["react", "vite", "tailwind"],
    },
    {
      id: "repo_def_2",
      name: "async-task-orchestrator",
      description: "Distributed task orchestrator built with async workers and redis stream persistence.",
      language: "Python",
      stars: 195,
      forks: 42,
      repoUrl: "https://github.com",
      topics: ["python", "redis"],
    },
  ];
  const portfolioItems = (b as any).portfolio ?? [
    {
      id: "port_def_1",
      title: "Cloud Scale Monitoring Dashboard",
      description: "Real-time metrics aggregator and latency visualization suite for microservices.",
      link: "https://github.com",
      role: "Full Stack Engineer",
      tags: ["React", "TypeScript", "TailwindCSS"],
      year: "2025",
    },
  ];
  const experienceEntries = (b as any).experienceEntries ?? [
    {
      title: b.role,
      company: b.company || "Tech Innovators",
      experienceLevel: b.experienceLevel || "Senior",
      period: "2022 – Present",
      description: "Designing reliable cloud infrastructures and scalable user interfaces.",
    },
  ];

  const { data: followStatus } = useFollowStatus(b.id);
  const followerCount = followStatus?.follower_count ?? b.followers ?? 0;
  const profileProjects = projects.filter(
    (project) =>
      project.owner === b.name ||
      project.owner === b.handle ||
      project.owner_id === b.id ||
      project.ownerId === b.id,
  );
  const userProjects = profileProjects;
  const isUserLoading = false;
  const isUserError = false;
  const profileAction = (
    <Link
      to="/settings"
      className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
    >
      Update profile
    </Link>
  );

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
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(b?.avatar);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isManageSkillsOpen, setIsManageSkillsOpen] = useState(false);
  const [followersModalType, setFollowersModalType] = useState<"followers" | "following" | null>(null);

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
        <Card className="p-4 sm:p-5 bg-gradient-to-r from-primary-soft via-transparent to-transparent border-primary/20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <TypoSection>
                <span className="text-base">🚀</span> Public Developer Showcase & Networking Profile
              </TypoSection>
              <TypoCaption as="p">
                Share your verified skills, experience, certifications, and portfolio with recruiters and collaborators.
              </TypoCaption>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link
                to="/portfolio/$username"
                params={{ username: b.handle }}
                className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                View Portfolio
              </Link>
              <button
                onClick={() => {
                  const url = `${window.location.origin}/portfolio/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Portfolio link copied to clipboard!");
                }}
                className="inline-flex items-center justify-center rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
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
        <Card className="p-3.5 bg-muted/40">
          <div className="flex items-center justify-between gap-3">
            <TypoCaption as="p">
              Looking for a polished portfolio showcase of {b.name}'s work?
            </TypoCaption>
            <Link
              to="/portfolio/$username"
              params={{ username: b.handle }}
              className="inline-flex items-center justify-center rounded-md border border-primary text-primary hover:bg-primary-soft px-3 py-1 text-xs font-semibold transition-colors shrink-0"
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
            education: headline,
            githubUrl: b.githubUrl,
            portfolioUrl: b.portfolioUrl,
            projects: userProjects.length,
          }}
        />
      )}

      {/* Main Profile Header Card */}
      <Card
        className={cn(
          "overflow-hidden p-0",
          b.premium && "border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.08)]",
        )}
      >
        {/* Cover Banner */}
        <div className="group relative h-36 sm:h-44 w-full overflow-hidden bg-muted">
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
              className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-md bg-black/60 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm transition-all hover:bg-black/80 cursor-pointer"
            >
              <Camera size={13} />
              Edit cover
            </button>
          )}
        </div>

        <div className="p-4 sm:p-5 pt-0">
          <div className="flex flex-wrap items-start gap-4 -mt-10 sm:-mt-12">
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
              className="ring-4 ring-card shadow-md"
            />
            <div className="min-w-0 flex-1 pt-10 sm:pt-4">
              <div className="flex flex-wrap items-center gap-2">
                <TypoHeading as="h1">
                  {b.name}
                  {b.verified &&
                    (b.premium ? (
                      <span className="inline-flex items-center gap-1.5 ml-1.5">
                        <BadgeCheck
                          className="text-amber-500 fill-amber-500/10 h-5 w-5 animate-pulse"
                          aria-label="Premium Verified User"
                        />
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 border border-amber-500/30 text-amber-500 px-2 py-0.5 rounded-full shadow-[0_0_8px_rgba(245,158,11,0.2)] animate-pulse">
                          PRO VERIFIED
                        </span>
                      </span>
                    ) : (
                      <BadgeCheck className="text-primary h-5 w-5 ml-1.5 inline" aria-label="Verified User" />
                    ))}
                </TypoHeading>

                {/* Open to Work Badge */}
                {openToWork && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Open to Work
                  </span>
                )}
              </div>

              {/* Professional Headline */}
              <p className="mt-1 text-xs sm:text-sm font-medium text-foreground leading-snug">
                {headline}
              </p>

              <TypoCaption as="p">
                @{b.handle} {b.role ? `· ${b.role}` : ""}
              </TypoCaption>

              {/* Availability & Collaboration Status */}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground bg-muted/50 px-2 py-0.5 rounded-md border border-border/50">
                  <Briefcase size={11} className="text-primary" />
                  <span>Availability: <strong>{availability}</strong></span>
                </span>

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

              {/* Networking details: location, website, metrics */}
              <div className="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <MapPin size={12} /> {b.location || b.country || "Remote"}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Calendar size={12} /> Joined 2024
                </span>
                {website && (
                  <a
                    href={website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-primary hover:underline"
                  >
                    <Globe size={12} /> {website.replace(/^https?:\/\//, "")}
                  </a>
                )}
              </div>

              <div className="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground border-t border-border/50 pt-2">
                <button
                  type="button"
                  onClick={() => setFollowersModalType("followers")}
                  className="hover:underline cursor-pointer focus:outline-none flex items-center gap-1"
                >
                  <span className="font-semibold text-foreground">{followerCount}</span>{" "}
                  <TypoCaption>Followers</TypoCaption>
                </button>
                <button
                  type="button"
                  onClick={() => setFollowersModalType("following")}
                  className="hover:underline cursor-pointer focus:outline-none flex items-center gap-1"
                >
                  <span className="font-semibold text-foreground">
                    {followStatus?.following_count ?? b.following ?? 0}
                  </span>{" "}
                  <TypoCaption>Following</TypoCaption>
                </button>
                <div>
                  <span className="font-semibold text-foreground">{b.contributions ?? 0}</span>{" "}
                  <TypoCaption>Contributions</TypoCaption>
                </div>
              </div>
            </div>

            {/* Header Action Buttons */}
            <div className="flex items-center gap-2 shrink-0">
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
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  <MessageCircle size={14} />
                  Contact
                </button>
              )}
              {me && (
                <Link
                  to="/profile-analytics"
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  <TrendingUp size={14} />
                  Analytics
                </Link>
              )}
              <button
                type="button"
                onClick={() => {
                  const url = `${window.location.origin}/profile/${b.handle}`;
                  navigator.clipboard.writeText(url);
                  toast.success("Profile link copied to clipboard!");
                }}
                className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
              >
                <LinkIcon size={13} />
                Copy Link
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* AI Profile Summary Section */}
      <Card className="p-3.5 sm:p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <Sparkles size={13} className="text-primary" />
            AI Professional Summary
          </p>
          {summary && !isEditing && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleEdit}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground cursor-pointer"
              >
                <Pencil size={11} /> Edit
              </button>
              <button
                onClick={() => summaryMutation.mutate()}
                disabled={summaryMutation.isPending}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground disabled:opacity-50 cursor-pointer"
              >
                <RotateCw size={11} className={summaryMutation.isPending ? "animate-spin" : ""} />{" "}
                Regenerate
              </button>
            </div>
          )}
          {!summary && !summaryMutation.isPending && (
            <button
              onClick={() => summaryMutation.mutate()}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-[11px] font-semibold text-primary-foreground hover:opacity-90"
            >
              <Sparkles size={11} /> Generate Summary
            </button>
          )}
        </div>

        {summaryMutation.isPending && (
          <div className="mt-2 space-y-1.5">
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-5/6" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>
        )}

        {summary && !summaryMutation.isPending && (
          <div className="mt-2 text-xs text-foreground leading-relaxed">
            {isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  maxLength={500}
                  rows={3}
                  className="w-full rounded-md border border-border bg-surface px-2.5 py-1.5 text-xs text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 resize-none"
                />
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground">{editedSummary.length}/500 chars</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={handleCancel}
                      className="rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      className="rounded-md bg-primary px-2.5 py-1 text-[11px] font-semibold text-primary-foreground"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <p>{summary}</p>
            )}
          </div>
        )}

        {!summary && !summaryMutation.isPending && (
          <TypoCaption as="p" className="mt-1">
            Generate an AI-powered summary highlighting skills, experience, and background.
          </TypoCaption>
        )}
      </Card>

      {me && <ProfileViewersList />}

      {/* Reputation and Trust Score Card */}
      <ReputationTrustCard
        userId={b.id}
        username={b.name}
        reputationScore={b.matchScore ? b.matchScore * 5 : 240}
        trustScore={b.verified ? 78 : 45}
        trustLevel={b.verified ? "Verified Contributor 🛡️" : "Active Community Member 🚀"}
        rankTier={(b as any).reputation_score ? ((b as any).reputation_score > 500 ? "Mentor 💎" : "Builder 🥇") : "Builder 🥇"}
        isVerified={b.verified}
        isSelf={me}
        onEndorse={async (skillOrReason, note) => {
          await reputationApi.endorseUser({
            target_user_id: b.id,
            skill_or_reason: skillOrReason,
            note,
          });
          toast.success(`Endorsed ${b.name} for ${skillOrReason}!`);
        }}
      />

      {/* Main 2-Column Professional Profile Grid */}
      <div className="grid gap-4 lg:grid-cols-12 items-start">
        {/* Left Column (5 cols) - Experience, Education, Certifications, Achievements */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Experience Card */}
          <ExperienceCard
            role={b.role}
            company={b.company}
            experienceLevel={b.experienceLevel}
            entries={experienceEntries}
            emptyAction={me ? profileAction : undefined}
          />

          {/* Education Card */}
          <EducationCard education={education} />

          {/* Certifications Card */}
          <CertificationsCard certifications={certifications} />

          {/* Achievements Card */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2.5">
              <Award size={15} className="text-amber-500" />
              <p className="text-xs font-semibold text-foreground">Achievements & Badges</p>
            </div>
            {b.badges && b.badges.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {b.badges.map((badge) => (
                  <span
                    key={badge}
                    className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary"
                  >
                    <span>🏅</span> {badge}
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
        </div>

        {/* Right Column (7 cols) - Skills, Featured Repos, Portfolio Showcase, Projects, Timeline */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          {/* Skills Matrix Card */}
          <SkillsCard
            skills={
              b.profileSkills && b.profileSkills.length > 0
                ? b.profileSkills
                : currentUser.profileSkills
            }
            emptyAction={me ? profileAction : undefined}
          />

          {/* Featured Repositories Card */}
          <FeaturedRepositoriesCard repositories={featuredRepositories} />

          {/* Portfolio Showcase Card */}
          <PortfolioShowcaseCard items={portfolioItems} />

          {/* Projects Card */}
          <Card className="p-4">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <FolderKanban size={15} className="text-primary" />
                <p className="text-xs font-semibold text-foreground">Active Projects</p>
              </div>
              {me && (
                <Link to="/projects" search={{ create: true }} className="text-[11px] font-medium text-primary hover:underline">
                  + Add Project
                </Link>
              )}
            </div>
            {profileProjects.length === 0 ? (
              <EmptyState
                icon={FolderKanban}
                title="No projects listed"
                desc="Projects showcase real-world development achievements."
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
                className="py-6"
              />
            ) : (
              <ul className="divide-y divide-border/60">
                {profileProjects.slice(0, 4).map((p) => (
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
                      <span className="grid h-7 w-7 place-items-center rounded-md bg-muted text-base shrink-0">
                        {p.icon || "🚀"}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-semibold text-foreground hover:text-primary transition-colors">
                          {p.name}
                        </p>
                        <TypoCaption as="p">{p.stack.join(" · ")}</TypoCaption>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {/* GitHub / Contribution Heatmap */}
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
                <div>
                  <GitHubInsights username={githubUsername} />
                </div>
              );
            }
            return <ContributionHeatmap username={b.handle} />;
          })()}

          {/* Activity Timeline */}
          <ActivityTimeline userId={b.id} emptyAction={me ? profileAction : undefined} />
          {me && (
            <ProfileViewersList
              isPremium={currentUser?.premium ?? true}
              className="mt-6"
            />
          )}
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
            firstName: b.firstName || "",
            lastName: b.lastName || "",
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

      <FollowersListModal
        isOpen={followersModalType !== null}
        onClose={() => setFollowersModalType(null)}
        userId={b.id}
        username={b.handle}
        type={followersModalType ?? "followers"}
      />
    </div>
  );
}

export default ProfilePage;
