import React, { useState, useMemo } from "react";
import { 
  CheckCircle2, 
  Circle, 
  User, 
  FileText, 
  Code2, 
  Github, 
  Globe, 
  Briefcase,
  ChevronDown,
  ChevronUp,
  Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface UserProfileData {
  avatar?: string;
  bio?: string;
  skills?: string[];
  githubUrl?: string;
  portfolioUrl?: string;
  experience?: string | number;
}

interface ChecklistItem {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  completed: boolean;
  actionText: string;
  href?: string;
}

interface ProfileCompletionChecklistProps {
  userProfile?: UserProfileData;
  onActionClick?: (itemId: string) => void;
  className?: string;
}

export function ProfileCompletionChecklist({
  userProfile = {},
  onActionClick,
  className,
}: ProfileCompletionChecklistProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Evaluate completion dynamically based on user profile state
  const items: ChecklistItem[] = useMemo(() => {
    return [
      {
        id: "avatar",
        label: "Upload avatar",
        description: "Add a profile photo so collaborators recognize you.",
        icon: User,
        completed: Boolean(userProfile.avatar && userProfile.avatar.trim() !== ""),
        actionText: "Upload photo",
      },
      {
        id: "bio",
        label: "Add bio",
        description: "Write a short summary about your background and interests.",
        icon: FileText,
        completed: Boolean(userProfile.bio && userProfile.bio.trim() !== ""),
        actionText: "Add bio",
      },
      {
        id: "skills",
        label: "Add skills",
        description: "List languages, frameworks, and tools you excel in.",
        icon: Code2,
        completed: Boolean(userProfile.skills && userProfile.skills.length > 0),
        actionText: "Add skills",
      },
      {
        id: "github",
        label: "Connect GitHub",
        description: "Link your GitHub account to highlight public repositories.",
        icon: Github,
        completed: Boolean(userProfile.githubUrl && userProfile.githubUrl.trim() !== ""),
        actionText: "Connect account",
      },
      {
        id: "portfolio",
        label: "Add portfolio",
        description: "Add a link to your personal website or portfolio.",
        icon: Globe,
        completed: Boolean(userProfile.portfolioUrl && userProfile.portfolioUrl.trim() !== ""),
        actionText: "Add link",
      },
      {
        id: "experience",
        label: "Add experience",
        description: "Specify your work or open-source experience duration.",
        icon: Briefcase,
        completed: Boolean(
          userProfile.experience !== undefined &&
            userProfile.experience !== null &&
            userProfile.experience !== ""
        ),
        actionText: "Add experience",
      },
    ];
  }, [userProfile]);

  const completedCount = useMemo(
    () => items.filter((item) => item.completed).length,
    [items]
  );

  const percentage = Math.round((completedCount / items.length) * 100);

  // Don't render or auto-hide if fully completed
  if (percentage === 100) {
    return null;
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-card p-4 transition-all shadow-sm",
        className
      )}
    >
      {/* Header & Progress Gauge */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">
                Complete your profile
              </h3>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                {percentage}%
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {completedCount} of {items.length} tasks completed
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label={isCollapsed ? "Expand checklist" : "Collapse checklist"}
        >
          {isCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Checklist Task Items */}
      {!isCollapsed && (
        <div className="mt-4 divide-y divide-border/50">
          {items.map((item) => {
            const IconComponent = item.icon;
            return (
              <div
                key={item.id}
                className="flex items-center justify-between py-2.5 text-xs transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  {item.completed ? (
                    <CheckCircle2 size={16} className="text-primary shrink-0" />
                  ) : (
                    <Circle size={16} className="text-muted-foreground shrink-0" />
                  )}
                  <IconComponent
                    size={14}
                    className={cn(
                      "shrink-0",
                      item.completed ? "text-primary" : "text-muted-foreground"
                    )}
                  />
                  <div className="min-w-0">
                    <p
                      className={cn(
                        "font-medium truncate",
                        item.completed
                          ? "line-through text-muted-foreground"
                          : "text-foreground"
                      )}
                    >
                      {item.label}
                    </p>
                    {!item.completed && (
                      <p className="text-[11px] text-muted-foreground truncate hidden sm:block">
                        {item.description}
                      </p>
                    )}
                  </div>
                </div>

                {!item.completed && (
                  <button
                    type="button"
                    onClick={() => onActionClick && onActionClick(item.id)}
                    className="shrink-0 rounded border border-border px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted hover:border-primary/40 transition-colors"
                  >
                    {item.actionText}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}