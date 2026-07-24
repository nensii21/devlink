import { Card } from "@/components/shared/primitives";
import { Flame, Sparkles, TrendingUp } from "lucide-react";
import { currentUser } from "@/mocks/seed";

export function GreetingHero() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good Morning" : hour < 18 ? "Good Afternoon" : "Good Evening";
  const first = currentUser.name.split(" ")[0];

  return (
    <Card className="relative overflow-hidden p-6 bg-surface border-border/80 shadow-soft">
      {/* Subtle ambient background glow */}
      <div className="pointer-events-none absolute -right-12 -top-12 h-48 w-48 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative z-10 flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
            {greeting}, <span className="text-primary">{first}</span>! 👋
          </h1>
          <p className="mt-1.5 text-[13px] font-medium text-muted-foreground">
            Welcome back to your developer hub. Here's your overview for today.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:w-auto shrink-0">
          <MiniStat
            icon={<TrendingUp size={16} />}
            tint="bg-blue-500/10 text-blue-500"
            label="Project Progress"
            value="75%"
            progress={75}
          />
          <MiniStat
            icon={<Flame size={16} />}
            tint="bg-amber-500/10 text-amber-500"
            label="Contribution Streak"
            value="12 days"
          />
          <MiniStat
            icon={<Sparkles size={16} />}
            tint="bg-emerald-500/10 text-emerald-500"
            label="AI Score"
            value="96"
            suffix="/100"
            valueTint="text-emerald-500"
          />
        </div>
      </div>
    </Card>
  );
}

function MiniStat({
  icon,
  tint,
  label,
  value,
  suffix,
  valueTint,
  progress,
}: {
  icon: React.ReactNode;
  tint: string;
  label: string;
  value: string;
  suffix?: string;
  valueTint?: string;
  progress?: number;
}) {
  return (
    <div className="group flex items-center gap-3 rounded-xl border border-border/80 bg-surface/90 p-3.5 shadow-xs transition-all duration-200 hover:border-primary/40 hover:shadow-card backdrop-blur-sm sm:min-w-[160px]">
      <span
        className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl transition-transform duration-200 group-hover:scale-105 ${tint}`}
      >
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="text-[16px] font-extrabold leading-tight tracking-tight text-foreground">
          <span className={valueTint}>{value}</span>
          {suffix && (
            <span className="text-[11px] font-medium text-muted-foreground">{suffix}</span>
          )}
        </p>
        {progress !== undefined && (
          <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary to-blue-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
