import React from "react";
import { cn } from "@/lib/utils";
import { Signal, SignalLow, SignalMedium, SignalHigh } from "lucide-react";

export type DifficultyLevel = "Beginner" | "Intermediate" | "Advanced";

interface ProjectDifficultyBadgeProps {
  difficulty?: DifficultyLevel | string;
  className?: string;
  showIcon?: boolean;
}

const difficultyStyles: Record<
  DifficultyLevel,
  { bg: string; text: string; border: string; icon: React.ElementType }
> = {
  Beginner: {
    bg: "bg-emerald-500/10 dark:bg-emerald-500/20",
    text: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-500/20 dark:border-emerald-500/30",
    icon: SignalLow,
  },
  Intermediate: {
    bg: "bg-amber-500/10 dark:bg-amber-500/20",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-500/20 dark:border-amber-500/30",
    icon: SignalMedium,
  },
  Advanced: {
    bg: "bg-rose-500/10 dark:bg-rose-500/20",
    text: "text-rose-600 dark:text-rose-400",
    border: "border-rose-500/20 dark:border-rose-500/30",
    icon: SignalHigh,
  },
};

export function ProjectDifficultyBadge({
  difficulty = "Beginner",
  className,
  showIcon = true,
}: ProjectDifficultyBadgeProps) {
  // Normalize string input to match valid DifficultyLevel keys
  const levelKey = (
    Object.keys(difficultyStyles).includes(difficulty) ? difficulty : "Beginner"
  ) as DifficultyLevel;

  const style = difficultyStyles[levelKey];
  const Icon = style.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold transition-colors",
        style.bg,
        style.text,
        style.border,
        className,
      )}
    >
      {showIcon && <Icon size={12} className="shrink-0" />}
      <span>{levelKey}</span>
    </span>
  );
}
