import { Card } from "@/components/shared/primitives";
import { Flame, Sparkles, TrendingUp } from "lucide-react";
import { currentUser } from "@/mocks/seed";

export function GreetingHero() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good Morning" : hour < 18 ? "Good Afternoon" : "Good Evening";
  const first = currentUser.name.split(" ")[0];

  return (
    <Card className="p-4">
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
        <div className="min-w-0">
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">
            {greeting}, {first}! <span aria-hidden>👋</span>
          </h1>
          <p className="mt-1 text-[13px] italic text-muted-foreground">
            "Code is like humor. When you have to explain it, it's bad." — Cory House
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 md:min-w-[520px]">
          <MiniStat
            icon={<TrendingUp size={16} />}
            tint="bg-info/10 text-info"
            label="Project Progress"
            value="75%"
            progress={75}
          />
          <MiniStat
            icon={<Flame size={16} />}
            tint="bg-warning/10 text-warning"
            label="Contribution Streak"
            value="12 days"
          />
          <MiniStat
            icon={<Sparkles size={16} />}
            tint="bg-primary-soft text-primary"
            label="AI Productivity Score"
            value="96"
            suffix="/100"
            valueTint="text-success"
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
    <div className="flex items-center gap-3 rounded-md border border-border bg-background/50 p-3">
      <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-md ${tint}`}>
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[11px] font-medium text-muted-foreground">{label}</p>
        <p className="text-[15px] font-bold text-foreground">
          <span className={valueTint}>{value}</span>
          {suffix && (
            <span className="text-[12px] font-medium text-muted-foreground">{suffix}</span>
          )}
        </p>
        {progress !== undefined && (
          <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-primary" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
    </div>
  );
}
