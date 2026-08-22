import React, { useState, useMemo } from "react";
import {
  Sparkles,
  X,
  ChevronRight,
  CheckCircle2,
  Circle,
  Trophy,
  Award,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export interface UserProfileData {
  avatar?: string;
  banner?: string;
  bio?: string;
  skills?: string[];
  experience?: string | number;
  education?: string;
  githubUrl?: string;
  linkedinUrl?: string;
  portfolioUrl?: string;
  website?: string;
  projects?: string[] | number;
}

interface ProfileCompletionChecklistProps {
  userProfile?: UserProfileData;
  className?: string;
}

export function ProfileCompletionChecklist({
  userProfile = {},
  className,
}: ProfileCompletionChecklistProps) {
  const [dismissed, setDismissed] = useState(false);
  const [showChecklist, setShowChecklist] = useState(false);

  const checklistItems = useMemo(() => {
    const hasAvatar = Boolean(userProfile.avatar?.trim());
    const hasBanner = Boolean(userProfile.banner?.trim());
    const hasBio = Boolean(userProfile.bio?.trim());
    const hasSkills = Boolean(userProfile.skills && userProfile.skills.length > 0);
    const hasExp = Boolean(
      userProfile.experience !== undefined &&
      userProfile.experience !== null &&
      userProfile.experience !== "",
    );
    const hasEdu = Boolean(userProfile.education?.trim());
    const hasSocial = Boolean(
      userProfile.githubUrl?.trim() ||
      userProfile.linkedinUrl?.trim() ||
      userProfile.portfolioUrl?.trim() ||
      userProfile.website?.trim(),
    );
    const hasProjects = Boolean(
      (Array.isArray(userProfile.projects) && userProfile.projects.length > 0) ||
      (typeof userProfile.projects === "number" && userProfile.projects > 0),
    );

    return [
      { id: "avatar", label: "Avatar Image", completed: hasAvatar },
      { id: "banner", label: "Cover Banner", completed: hasBanner },
      { id: "bio", label: "Developer Bio", completed: hasBio },
      { id: "skills", label: "Skills & Tech Stack", completed: hasSkills },
      { id: "experience", label: "Work Experience", completed: hasExp },
      { id: "education", label: "Education & Headline", completed: hasEdu },
      { id: "social", label: "Social & Portfolio Links", completed: hasSocial },
      { id: "projects", label: "Featured Projects", completed: hasProjects },
    ];
  }, [userProfile]);

  const completedCount = useMemo(() => {
    return checklistItems.filter((i) => i.completed).length;
  }, [checklistItems]);

  const totalItems = 8;
  const percentage = Math.round((completedCount / totalItems) * 100);

  if (dismissed) {
    return null;
  }

  // 100% Celebration Reward Banner
  if (percentage === 100) {
    return (
      <div
        className={cn(
          "relative overflow-hidden rounded-xl bg-gradient-to-r from-amber-500/20 via-amber-500/10 to-card border border-amber-500/30 p-4 transition-all shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in duration-300",
          className,
        )}
      >
        <div className="flex items-center gap-4 flex-1">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-amber-500 ring-2 ring-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.3)]">
            <Trophy size={22} className="animate-bounce" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <TypoSection>100% Profile Complete!</TypoSection>
              <span className="rounded-full bg-amber-500/20 border border-amber-500/40 px-2 py-0.5 text-[10px] font-bold text-amber-500 flex items-center gap-1">
                <Award size={10} /> Profile Master Unlocked
              </span>
            </div>
            <TypoCaption as="p">
              Congratulations! Your profile is fully complete. You have earned the exclusive{" "}
              <strong className="text-amber-500 font-semibold">Profile Master</strong> badge!
            </TypoCaption>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
          <button
            onClick={() => setDismissed(true)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="Dismiss banner"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-background border border-primary/20 p-4 transition-all shadow-sm flex flex-col gap-3",
        className,
      )}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Sparkles size={20} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <TypoSection>Complete your profile</TypoSection>
              <span className="rounded-full bg-primary/20 px-2 py-0.5 text-[10px] font-bold text-primary">
                {percentage}%
              </span>
            </div>
            <TypoCaption as="p">
              Stand out to other builders and unlock the{" "}
              <strong className="text-primary font-medium">Profile Master</strong> reward badge. (
              {completedCount}/{totalItems} factors complete)
            </TypoCaption>
            <div className="mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-primary/10">
              <div
                className="h-full bg-primary transition-all duration-500 ease-out"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
          <button
            onClick={() => setShowChecklist((prev) => !prev)}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
          >
            {showChecklist ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {showChecklist ? "Hide Factors" : "View Factors"}
          </button>
          <Link
            to="/settings"
            className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Complete Now <ChevronRight size={14} />
          </Link>
          <button
            onClick={() => setDismissed(true)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="Dismiss banner"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Checklist breakdown */}
      {showChecklist && (
        <div className="mt-2 pt-3 border-t border-border/50 grid grid-cols-2 sm:grid-cols-4 gap-2 animate-in fade-in duration-200">
          {checklistItems.map((item) => (
            <div
              key={item.id}
              className={cn(
                "flex items-center gap-1.5 text-xs p-1.5 rounded-md transition-colors",
                item.completed
                  ? "text-foreground font-medium bg-emerald-500/10 border border-emerald-500/20"
                  : "text-muted-foreground bg-muted/30 border border-border/30",
              )}
            >
              {item.completed ? (
                <CheckCircle2 size={13} className="text-emerald-500 shrink-0" />
              ) : (
                <Circle size={13} className="text-muted-foreground/50 shrink-0" />
              )}
              <span className="truncate">{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
