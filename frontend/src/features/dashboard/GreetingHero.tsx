import { Card } from "@/components/shared/primitives";
import { Flame, Sparkles, TrendingUp, ArrowRight } from "lucide-react";
import { currentUser } from "@/mocks/seed";
import { Link } from "@tanstack/react-router";

export function GreetingHero() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const first = currentUser.name.split(" ")[0];

  return (
<Card className="flex flex-col gap-5 p-5 sm:p-6 sm:flex-row sm:items-center sm:justify-between">      <div className="min-w-0 flex-1">
        <h1 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
          {greeting}, {first}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Here's what's happening with your projects today.
        </p>
        <div className="mt-3 flex items-center gap-4">
          <Link
            to="/projects"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
          >
            View active projects <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      <div className="flex flex-row gap-3 sm:w-auto shrink-0 overflow-x-auto pb-1 sm:pb-0 hide-scrollbar">
        <MiniStat icon={<TrendingUp size={14} />} label="Progress" value="75%" progress={75} />
        <MiniStat icon={<Flame size={14} />} label="Streak" value="12d" />
        <MiniStat icon={<Sparkles size={14} />} label="AI Score" value="96" />
      </div>
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
<div className="flex flex-col justify-between gap-2 rounded-2xl border border-border/40 bg-muted/20 p-3.5 min-w-[120px] sm:min-w-[130px] shrink-0">      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <p className="text-[10px] font-medium uppercase tracking-wider truncate">{label}</p>
      </div>
      <div>
        <p className="text-lg font-semibold tracking-tight text-foreground">{value}</p>
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
