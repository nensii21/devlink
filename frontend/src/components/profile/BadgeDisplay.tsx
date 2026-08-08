import React from "react";
import { Award, Rocket, Users, Sparkles, HeartHandshake, Star } from "lucide-react";

export interface BadgeItem {
  id: string;
  slug: string;
  name: string;
  description: string;

  icon: string;
  category: string;
  points: number;
}

export interface UserBadgeItem {
  id: string;
  badge: BadgeItem;
  awarded_at: string;
}

interface BadgeDisplayProps {
  userBadges: UserBadgeItem[];
  allBadges?: BadgeItem[];
}

const ICON_MAP: Record<string, React.ElementType> = {
  rocket: Rocket,
  users: Users,
  award: Award,
  sparkles: Sparkles,
  "heart-handshake": HeartHandshake,
  star: Star,
};

export const BadgeDisplay: React.FC<BadgeDisplayProps> = ({ userBadges, allBadges = [] }) => {
  const earnedSlugs = new Set(userBadges.map((ub) => ub.badge.slug));

  const displayList = allBadges.length > 0 ? allBadges : userBadges.map((ub) => ub.badge);

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Award className="h-5 w-5 text-amber-500" />
          Achievement Badges
        </h2>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
          {userBadges.length} Earned
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mt-2">
        {displayList.map((badge) => {
          const isEarned = earnedSlugs.has(badge.slug) || allBadges.length === 0;
          const IconComp = ICON_MAP[badge.icon] || Award;

          return (
            <div
              key={badge.id || badge.slug}
              className={`flex flex-col items-center text-center p-3 rounded-lg border transition-all ${
                isEarned
                  ? "border-amber-500/30 bg-amber-500/5 hover:border-amber-500/60 shadow-xs"
                  : "border-border/40 bg-muted/30 opacity-50 grayscale"
              }`}
              title={badge.description}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${
                  isEarned
                    ? "bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-xs"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <IconComp className="h-5 w-5" />
              </div>
              <span className="text-xs font-semibold line-clamp-1 text-foreground">
                {badge.name}
              </span>
              <span className="text-[10px] text-muted-foreground mt-0.5">{badge.points} pts</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
