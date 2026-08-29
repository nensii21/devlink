import React from "react";
import { TrendingUp, Hash, Flame, Sparkles, MessageSquare } from "lucide-react";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";
import { cn } from "@/lib/utils";

export interface TrendingTopic {
  id: string;
  tag: string;
  category: string;
  postsCount: number;
  isHot?: boolean;
}

export const DEFAULT_TRENDING_TOPICS: TrendingTopic[] = [
  { id: "1", tag: "React19", category: "Frameworks", postsCount: 1420, isHot: true },
  { id: "2", tag: "FastAPI", category: "Backend", postsCount: 890, isHot: true },
  { id: "3", tag: "BuildInPublic", category: "Community", postsCount: 3240, isHot: false },
  { id: "4", tag: "Hackathons2026", category: "Events", postsCount: 640, isHot: true },
  { id: "5", tag: "AIProductivity", category: "Artificial Intelligence", postsCount: 1980, isHot: false },
  { id: "6", tag: "TypeScript5", category: "Languages", postsCount: 1120, isHot: false },
];

export interface TrendingSidebarProps {
  topics?: TrendingTopic[];
  onSelectTopic?: (tag: string) => void;
  className?: string;
}

export function TrendingSidebar({
  topics = DEFAULT_TRENDING_TOPICS,
  onSelectTopic,
  className,
}: TrendingSidebarProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-card p-4 shadow-sm space-y-4", className)}>
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <TypoSection as="h3" className="text-sm font-semibold">Trending Topics</TypoSection>
        </div>
        <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
      </div>

      <div className="space-y-3">
        {topics.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelectTopic?.(item.tag)}
            className="w-full group flex items-start justify-between rounded-xl p-2.5 hover:bg-surface border border-transparent hover:border-border/60 transition-all text-left cursor-pointer"
          >
            <div className="space-y-0.5 min-w-0 flex-1">
              <div className="flex items-center gap-1.5 font-medium text-xs text-foreground group-hover:text-primary transition-colors">
                <Hash className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary" />
                <span className="truncate">{item.tag}</span>
                {item.isHot && <Flame className="h-3.5 w-3.5 text-amber-500 fill-amber-500/20 shrink-0" />}
              </div>
              <div className="text-[11px] text-muted-foreground flex items-center gap-2">
                <span>{item.category}</span>
                <span>•</span>
                <span>{item.postsCount.toLocaleString()} posts</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default TrendingSidebar;
