import React, { useState, useMemo } from "react";
import { Sparkles, X, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";

export interface UserProfileData {
  avatar?: string;
  bio?: string;
  skills?: string[];
  githubUrl?: string;
  portfolioUrl?: string;
  experience?: string | number;
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

  const completedCount = useMemo(() => {
    let count = 0;
    if (userProfile.avatar?.trim()) count++;
    if (userProfile.bio?.trim()) count++;
    if (userProfile.skills && userProfile.skills.length > 0) count++;
    if (userProfile.githubUrl?.trim()) count++;
    if (userProfile.portfolioUrl?.trim()) count++;
    if (
      userProfile.experience !== undefined &&
      userProfile.experience !== null &&
      userProfile.experience !== ""
    )
      count++;
    return count;
  }, [userProfile]);

  const totalItems = 6;
  const percentage = Math.round((completedCount / totalItems) * 100);

  if (percentage === 100 || dismissed) {
    return null;
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-background border border-primary/20 p-4 transition-all shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4",
        className,
      )}
    >
      <div className="flex items-center gap-4 flex-1">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Sparkles size={20} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-foreground">Complete your profile</h3>
            <span className="rounded-full bg-primary/20 px-2 py-0.5 text-[10px] font-bold text-primary">
              {percentage}%
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Stand out to other builders. You have {totalItems - completedCount} tasks remaining.
          </p>
          <div className="mt-2 h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-primary/10">
            <div
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
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
  );
}
