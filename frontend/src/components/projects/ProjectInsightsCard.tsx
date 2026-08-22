import { useMutation } from "@tanstack/react-query";
import { Sparkles, Users2, AlertTriangle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { projectInsightsApi } from "@/api/modules/projectInsights";
import type { ProjectInsightsResponse } from "@/api/modules/projectInsights";
import { Skeleton } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import { TypoCaption } from "@/components/shared/Typography";

interface ProjectInsightsCardProps {
  projectId: string;
  title: string;
  description: string;
  techStack?: string[];
  status?: string;
  members?: number;
  /** Compact mode: single collapsed row for use inside listing cards */
  compact?: boolean;
}

const severityStyles = {
  info: "text-primary bg-primary/10 border-primary/20",
  warning: "text-warning bg-warning/10 border-warning/30",
  critical: "text-destructive bg-destructive/10 border-destructive/30",
} as const;

const urgencyDot = {
  low: "bg-success",
  medium: "bg-warning",
  high: "bg-destructive",
} as const;

export function ProjectInsightsCard({
  projectId,
  title,
  description,
  techStack,
  status,
  members,
  compact = false,
}: ProjectInsightsCardProps) {
  const [insights, setInsights] = useState<ProjectInsightsResponse | null>(null);
  const [expanded, setExpanded] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      projectInsightsApi.generate({
        project_id: projectId,
        title,
        description,
        tech_stack: techStack?.join(", "),
        status,
        members,
      }),
    onSuccess: (data) => {
      setInsights(data);
      setExpanded(true);
    },
  });

  const handleToggle = () => {
    if (!insights && !mutation.isPending) {
      mutation.mutate();
    } else {
      setExpanded((v) => !v);
    }
  };

  if (compact) {
    return (
      <div className="mt-3 border-t border-border pt-3">
        <button
          onClick={(e) => {
            e.preventDefault();
            handleToggle();
          }}
          className="inline-flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground hover:text-primary transition-colors"
          aria-expanded={expanded}
          aria-label="Toggle AI insights"
        >
          <Sparkles size={11} className={cn(mutation.isPending && "animate-pulse text-primary")} />
          AI Insights
          {!mutation.isPending && (expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />)}
        </button>

        {mutation.isPending && (
          <div className="mt-2 space-y-1.5">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        )}

        {expanded && insights && (
          <div className="mt-2 space-y-2">
            {insights.summary && <TypoCaption as="p">{insights.summary}</TypoCaption>}

            {insights.risk_alerts.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {insights.risk_alerts.slice(0, 2).map((alert, i) => (
                  <span
                    key={i}
                    className={cn(
                      "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium",
                      severityStyles[alert.severity],
                    )}
                  >
                    <AlertTriangle size={9} />
                    {alert.message}
                  </span>
                ))}
              </div>
            )}

            {insights.role_gaps.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {insights.role_gaps.slice(0, 2).map((gap, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                  >
                    <span className={cn("h-1.5 w-1.5 rounded-full", urgencyDot[gap.urgency])} />
                    {gap.role} needed
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Full card mode (used in project detail)
  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="flex items-center gap-2 text-[13px] font-semibold text-foreground">
          <Sparkles size={14} className="text-primary" />
          AI Insights
        </p>
        <button
          onClick={handleToggle}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors"
          aria-expanded={expanded}
        >
          {mutation.isPending
            ? "Generating…"
            : insights
              ? expanded
                ? "Hide"
                : "Show"
              : "Generate"}
          {!mutation.isPending &&
            insights &&
            (expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />)}
        </button>
      </div>

      {mutation.isPending && (
        <div className="mt-3 space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}

      {mutation.isError && (
        <p className="mt-2 text-[11px] text-destructive">Failed to generate insights. Try again.</p>
      )}

      {expanded && insights && (
        <div className="mt-3 space-y-4">
          {/* Summary */}
          {insights.summary && <TypoCaption as="p">{insights.summary}</TypoCaption>}

          {/* Suggested builders */}
          {insights.suggested_builders.length > 0 && (
            <div>
              <TypoCaption as="p">
                <Users2 size={11} />
                Suggested Roles
              </TypoCaption>
              <div className="space-y-1.5">
                {insights.suggested_builders.map((b, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-[12px] text-foreground">{b.name}</span>
                    <TypoCaption>{Math.round(b.match_score * 100)}% match</TypoCaption>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Role gaps */}
          {insights.role_gaps.length > 0 && (
            <div>
              <TypoCaption as="p">Role Gaps</TypoCaption>
              <div className="flex flex-wrap gap-1.5">
                {insights.role_gaps.map((gap, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 rounded-md border border-border/60 bg-muted/60 px-2 py-1 text-[11px] text-muted-foreground"
                  >
                    <span className={cn("h-2 w-2 rounded-full", urgencyDot[gap.urgency])} />
                    {gap.role}
                    <span className="text-[10px] capitalize opacity-70">· {gap.urgency}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Risk alerts */}
          {insights.risk_alerts.length > 0 && (
            <div>
              <TypoCaption as="p">
                <AlertTriangle size={11} />
                Risk Alerts
              </TypoCaption>
              <div className="space-y-1.5">
                {insights.risk_alerts.map((alert, i) => (
                  <div
                    key={i}
                    className={cn(
                      "flex items-start gap-2 rounded-md border px-2.5 py-2 text-[11px] font-medium",
                      severityStyles[alert.severity],
                    )}
                  >
                    <Info size={12} className="mt-px shrink-0" />
                    {alert.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
