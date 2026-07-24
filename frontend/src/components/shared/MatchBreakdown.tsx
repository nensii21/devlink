import { Card } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import type { ScoreBreakdown } from "@/matching/types";

const CRITERIA_CONFIG = [
  { key: "skills" as const, label: "Skills", description: "Technical skill alignment" },
  { key: "experience" as const, label: "Experience", description: "Years of experience match" },
  { key: "interests" as const, label: "Interests", description: "Domain interest overlap" },
  { key: "availability" as const, label: "Availability", description: "Hours per week match" },
  { key: "collaboration" as const, label: "Collaboration", description: "Previous work history" },
];

function getBarColor(score: number): string {
  if (score >= 80) return "bg-success";
  if (score >= 60) return "bg-primary";
  if (score >= 40) return "bg-warning";
  return "bg-destructive";
}

export function MatchBreakdown({ breakdown }: { breakdown: ScoreBreakdown }) {
  return (
    <Card className="p-4">
      <p className="text-[13px] font-semibold text-foreground">Score Breakdown</p>
      <div className="mt-3 space-y-3">
        {CRITERIA_CONFIG.map(({ key, label, description }) => (
          <div key={key}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[12px] font-medium text-foreground">{label}</p>
                <p className="text-[10px] text-muted-foreground">{description}</p>
              </div>
              <span className="text-[12px] font-bold text-foreground">{breakdown[key]}%</span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className={cn("h-full rounded-full transition-all", getBarColor(breakdown[key]))}
                style={{ width: `${breakdown[key]}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
