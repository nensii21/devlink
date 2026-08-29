import React, { useState } from "react";
import { Users2, UserPlus, Check, Sparkles, Zap } from "lucide-react";
import { UserAvatar } from "@/components/user-avatar";
import { TypoSection, TypoCard, TypoCaption } from "@/components/shared/Typography";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface SuggestedBuilder {
  id: string;
  name: string;
  avatar?: string;
  headline: string;
  matchScore?: number;
  skills?: string[];
}

export const DEFAULT_SUGGESTED_BUILDERS: SuggestedBuilder[] = [
  {
    id: "b1",
    name: "Alex Rivera",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
    headline: "Full Stack Engineer @ DevTech",
    matchScore: 98,
    skills: ["React", "FastAPI"],
  },
  {
    id: "b2",
    name: "Dmitri Volkov",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    headline: "Rust & Distributed Systems",
    matchScore: 94,
    skills: ["Rust", "WebAssembly"],
  },
  {
    id: "b3",
    name: "Mei Lin",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
    headline: "AI/ML Engineer & Open Source Contributor",
    matchScore: 91,
    skills: ["Python", "PyTorch"],
  },
];

export interface SuggestedBuildersSidebarProps {
  builders?: SuggestedBuilder[];
  className?: string;
}

export function SuggestedBuildersSidebar({
  builders = DEFAULT_SUGGESTED_BUILDERS,
  className,
}: SuggestedBuildersSidebarProps) {
  const [followingMap, setFollowingMap] = useState<Record<string, boolean>>({});

  const toggleFollow = (id: string) => {
    setFollowingMap((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className={cn("rounded-2xl border border-border bg-card p-4 shadow-sm space-y-4", className)}>
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <Users2 className="h-4 w-4 text-primary" />
          <TypoSection as="h3" className="text-sm font-semibold">Suggested Builders</TypoSection>
        </div>
        <Sparkles className="h-3.5 w-3.5 text-amber-500" />
      </div>

      <div className="space-y-3.5">
        {builders.map((builder) => {
          const isFollowing = !!followingMap[builder.id];
          return (
            <div key={builder.id} className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5 min-w-0 flex-1">
                <UserAvatar src={builder.avatar} name={builder.name} size="sm" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <TypoCard className="text-xs font-semibold truncate text-foreground">{builder.name}</TypoCard>
                    {builder.matchScore && (
                      <span className="flex items-center gap-0.5 text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-1.5 py-0.2 rounded-full shrink-0">
                        <Zap size={10} /> {builder.matchScore}%
                      </span>
                    )}
                  </div>
                  <TypoCaption className="text-[11px] truncate block text-muted-foreground mt-0.5">
                    {builder.headline}
                  </TypoCaption>
                </div>
              </div>

              <Button
                variant={isFollowing ? "outline" : "default"}
                size="sm"
                onClick={() => toggleFollow(builder.id)}
                className="h-7 px-2.5 text-xs rounded-full gap-1 shrink-0"
              >
                {isFollowing ? (
                  <>
                    <Check size={12} />
                    <span>Following</span>
                  </>
                ) : (
                  <>
                    <UserPlus size={12} />
                    <span>Follow</span>
                  </>
                )}
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SuggestedBuildersSidebar;
