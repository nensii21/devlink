import { useQuery } from "@tanstack/react-query";
import { Award, Medal } from "lucide-react";
import { Card, EmptyState } from "@/components/shared/primitives";
import { hackathonsService } from "@/services";
import { cn } from "@/lib/utils";
import { TypoCaption } from "@/components/shared/Typography";

interface Props {
  hackathonId: string;
}

const RANK_STYLES: Record<number, { bg: string; text: string; label: string }> = {
  1: { bg: "bg-warning/10 border-warning/30", text: "text-warning", label: "1st" },
  2: { bg: "bg-muted border-border", text: "text-muted-foreground", label: "2nd" },
  3: { bg: "bg-primary/10 border-primary/30", text: "text-primary", label: "3rd" },
};

function getRankStyle(rank: number) {
  return (
    RANK_STYLES[rank] ?? {
      bg: "bg-muted/50 border-border",
      text: "text-muted-foreground",
      label: `${rank}th`,
    }
  );
}

export function LeaderboardTab({ hackathonId }: Props) {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ["hackathon-leaderboard", hackathonId],
    queryFn: () => hackathonsService.getLeaderboard(hackathonId),
    enabled: !!hackathonId,
  });

  if (isLoading) {
    return (
      <div className="space-y-2" aria-busy="true">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="h-16 animate-pulse" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <Card className="p-8">
        <EmptyState
          title="No scores yet"
          desc="The leaderboard will be populated after judging begins."
          icon={Award}
        />
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[13px] text-muted-foreground">
        Ranked by average judge score · {entries.length} team
        {entries.length !== 1 ? "s" : ""}
      </p>

      {/* Desktop table */}
      <div className="hidden w-full overflow-x-auto rounded-xl border border-border sm:block">
        <table className="w-full min-w-max border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-border bg-muted">
              <th
                scope="col"
                className="whitespace-nowrap px-4 py-3 text-left font-semibold text-foreground"
              >
                Rank
              </th>
              <th
                scope="col"
                className="whitespace-nowrap px-4 py-3 text-left font-semibold text-foreground"
              >
                Team
              </th>
              <th
                scope="col"
                className="whitespace-nowrap px-4 py-3 text-left font-semibold text-foreground"
              >
                Project
              </th>
              <th
                scope="col"
                className="whitespace-nowrap px-4 py-3 text-right font-semibold text-foreground"
              >
                Avg score
              </th>
              <th
                scope="col"
                className="whitespace-nowrap px-4 py-3 text-right font-semibold text-foreground"
              >
                Judges
              </th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => {
              const style = getRankStyle(entry.rank);
              return (
                <tr
                  key={entry.team_id}
                  className="border-b border-border transition-colors last:border-0 hover:bg-muted/50"
                >
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex h-7 w-7 items-center justify-center rounded-full border text-[12px] font-bold",
                        style.bg,
                        style.text,
                      )}
                      aria-label={`Rank ${style.label}`}
                    >
                      {entry.rank <= 3 ? <Medal size={13} /> : entry.rank}
                    </span>
                  </td>
                  <td className="break-words px-4 py-3 font-medium text-foreground">
                    {entry.team_name}
                  </td>
                  <td className="break-words px-4 py-3 text-muted-foreground">
                    {entry.submission_title}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ScoreBar score={entry.avg_score} />
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {entry.judge_count}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile card list */}
      <div className="space-y-2 sm:hidden">
        {entries.map((entry) => {
          const style = getRankStyle(entry.rank);
          return (
            <Card key={entry.team_id} className="p-4">
              <div className="flex items-start gap-3">
                <span
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-full border text-[13px] font-bold",
                    style.bg,
                    style.text,
                  )}
                  aria-label={`Rank ${style.label}`}
                >
                  {entry.rank <= 3 ? <Medal size={14} /> : entry.rank}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[14px] font-semibold text-foreground">{entry.team_name}</p>
                  <TypoCaption as="p" className="mt-0.5 text-[12px] text-muted-foreground">{entry.submission_title}</TypoCaption>
                  <div className="mt-2 flex items-center justify-between">
                    <ScoreBar score={entry.avg_score} />
                    <span className="text-[11px] text-muted-foreground">
                      {entry.judge_count} judge{entry.judge_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 80
      ? "bg-success"
      : pct >= 60
        ? "bg-primary"
        : pct >= 40
          ? "bg-warning"
          : "bg-destructive";

  return (
    <div className="inline-flex items-center gap-2">
      <div
        className="h-1.5 w-20 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Score: ${score}`}
      >
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[13px] font-semibold text-foreground tabular-nums">{score}</span>
    </div>
  );
}
