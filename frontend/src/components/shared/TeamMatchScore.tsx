import { Card } from "@/components/shared/primitives";
import { Progress } from "@/components/ui/progress";
import type { MatchResult } from "@/matching/types";
import { cn } from "@/lib/utils";

function getScoreColor(score: number): string {
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-primary";
  if (score >= 40) return "text-warning";
  return "text-destructive";
}

function getScoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Low";
}

export function TeamMatchScore({
  match,
  compact = false,
}: {
  match: MatchResult;
  compact?: boolean;
}) {
  const { totalScore, breakdown, summary } = match;

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className={cn("text-[14px] font-bold", getScoreColor(totalScore))}>
          {totalScore}%
        </span>
        <span className="text-[11px] text-muted-foreground">{getScoreLabel(totalScore)}</span>
      </div>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold text-foreground">AI Match Score</p>
        <span className={cn("text-[11px] font-medium", getScoreColor(totalScore))}>
          {getScoreLabel(totalScore)}
        </span>
      </div>
      <div className="mt-3 flex items-end gap-2">
        <span className={cn("text-[36px] font-bold leading-none", getScoreColor(totalScore))}>
          {totalScore}
        </span>
        <span className="mb-1 text-[14px] text-muted-foreground">/100</span>
      </div>
      <Progress value={totalScore} className="mt-3" />
      <div className="mt-4 space-y-2">
        {(
          [
            ["Skills", breakdown.skills],
            ["Experience", breakdown.experience],
            ["Interests", breakdown.interests],
            ["Availability", breakdown.availability],
            ["Collaboration", breakdown.collaboration],
          ] as const
        ).map(([label, value]) => (
          <div key={label} className="flex items-center justify-between text-[12px]">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium text-foreground">{value}%</span>
          </div>
        ))}
      </div>
      {summary.length > 0 && (
        <div className="mt-4 border-t border-border pt-3">
          <p className="mb-2 text-[12px] font-semibold text-foreground">Match Details</p>
          <ul className="space-y-1">
            {summary.map((item, idx) => (
              <li key={idx} className="text-[11px] text-muted-foreground">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
