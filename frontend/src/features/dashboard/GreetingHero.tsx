import { Card } from "@/components/shared/primitives";
import { Button } from "@/components/ui/button";
import {
  Folder,
  Users2,
  Calendar,
  ArrowRight,
  Plus,
  TrendingUp,
  Flame,
  Sparkles,
} from "lucide-react";
import { currentUser } from "@/mocks/seed";
import { Link } from "@tanstack/react-router";
import { TypoCaption, TypoHeading, TypoCard } from "@/components/shared/Typography";

export function GreetingHero() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const first = currentUser.name.split(" ")[0];

  return (
    <Card className="flex flex-col gap-4 p-4 sm:p-5 sm:flex-row sm:items-center sm:justify-between rounded-xl bg-card border-border/60 shadow-xs relative overflow-hidden">
      <div className="min-w-0 flex-1 flex flex-col gap-3">
        <div>
          <TypoHeading as="h1" className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            {greeting}, {first}! 👋
          </TypoHeading>
          <TypoCaption as="p" className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Here's what's happening with your workspace today.
          </TypoCaption>
        </div>

        {/* Inline Stats Badges Row */}
        <div className="flex flex-wrap gap-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border bg-surface shadow-2xs">
            <Folder size={13} className="text-primary" />
            <TypoCaption className="text-xs font-semibold text-foreground">2 Active Projects</TypoCaption>
          </div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border bg-surface shadow-2xs">
            <Users2 size={13} className="text-emerald-500" />
            <TypoCaption className="text-xs font-semibold text-foreground">3 Pending Invites</TypoCaption>
          </div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border bg-surface shadow-2xs">
            <Calendar size={13} className="text-violet-500" />
            <TypoCaption className="text-xs font-semibold text-foreground">5 Tasks Due</TypoCaption>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button asChild variant="primary" size="sm" className="gap-1.5 font-medium">
            <Link to="/projects">
              Continue Working <ArrowRight size={13} />
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm" className="gap-1.5 font-medium">
            <Link to="/projects">
              Create Project <Plus size={13} />
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2.5 sm:flex sm:w-auto sm:flex-row sm:shrink-0">
        <MiniStat icon={<TrendingUp size={13} />} label="Progress" value="75%" progress={75} />
        <MiniStat icon={<Flame size={13} />} label="Streak" value="12d" />
        <MiniStat icon={<Sparkles size={13} />} label="AI Score" value="96" />
      </div>
      {/* SVG Laptop/Plant Illustration */}
      <svg
        width="140"
        height="100"
        viewBox="0 0 180 130"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0 hidden xl:block select-none opacity-85 dark:opacity-40"
      >
        <rect x="25" y="15" width="130" height="85" rx="6" fill="var(--color-surface, #F8FAFC)" stroke="var(--color-border, #E2E8F0)" strokeWidth="2" />
        <rect x="29" y="19" width="122" height="73" rx="4" fill="var(--color-background, #FFFFFF)" />
        {/* Laptop screen interior mocks */}
        <rect x="35" y="25" width="30" height="20" rx="3" fill="#05B7D7" fillOpacity="0.08" stroke="#05B7D7" strokeWidth="1" strokeOpacity="0.2" />
        <rect x="70" y="25" width="30" height="20" rx="3" fill="#6366F1" fillOpacity="0.08" stroke="#6366F1" strokeWidth="1" strokeOpacity="0.2" />
        <rect x="105" y="25" width="38" height="20" rx="3" fill="#10B981" fillOpacity="0.08" stroke="#10B981" strokeWidth="1" strokeOpacity="0.2" />
        <rect x="35" y="52" width="60" height="32" rx="3" fill="var(--color-muted, #F1F5F9)" />
        <rect x="40" y="58" width="40" height="4" rx="2" fill="#CBD5E1" />
        <rect x="40" y="66" width="50" height="4" rx="2" fill="var(--color-border, #E2E8F0)" />
        <rect x="40" y="74" width="30" height="4" rx="2" fill="var(--color-border, #E2E8F0)" />
        <rect x="102" y="52" width="41" height="32" rx="3" fill="var(--color-muted, #F1F5F9)" />
        <circle cx="122" cy="68" r="10" fill="#05B7D7" fillOpacity="0.1" />

        {/* Laptop Base */}
        <path d="M10 100H170L165 106H15L10 100Z" fill="var(--color-muted, #E2E8F0)" stroke="var(--color-border, #CBD5E1)" strokeWidth="1.5" />
        <rect x="75" y="100" width="30" height="3" rx="1.5" fill="#94A3B8" />

        {/* Table Line */}
        <line x1="5" y1="120" x2="175" y2="120" stroke="var(--color-border, #E2E8F0)" strokeWidth="2" strokeLinecap="round" />

        {/* Plant Pot */}
        <path d="M152 120L150 110H162L160 120H152Z" fill="var(--color-muted, #E2E8F0)" stroke="var(--color-border, #CBD5E1)" strokeWidth="1.5" />
        {/* Leaves */}
        <path d="M156 110C156 102 153 96 150 94C153 96 156 102 156 110Z" fill="#10B981" />
        <path d="M156 110C156 100 162 94 165 92C162 94 156 100 156 110Z" fill="#10B981" />
        <path d="M156 110C152 108 147 106 145 102C147 106 152 108 156 110Z" fill="#10B981" />
      </svg>
    </Card>
  );
}

function MiniStat({
  icon,
  label,
  value,
  progress,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  progress?: number;
}) {
  return (
    <div className="flex flex-col justify-between gap-1.5 rounded-xl border border-border/50 bg-muted/20 p-3 sm:min-w-[120px] sm:shrink-0">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <TypoCaption as="p" className="text-[10px] font-medium uppercase tracking-wider truncate">
          {label}
        </TypoCaption>
      </div>
      <div>
        <TypoCard as="p" className="text-lg font-semibold tracking-tight text-foreground">
          {value}
        </TypoCard>
        {progress !== undefined && (
          <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-muted/50">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
