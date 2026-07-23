import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import { containerVariants, cardEntrance, STAGGER_DELAY } from "@/lib/animations";
import { repositoryQualityApi } from "@/api";
import type { RepositoryQualityResponse, MetricScore, ImprovementSuggestion } from "@/api";
import { cn } from "@/lib/utils";
import {
  Search,
  Star,
  GitFork,
  AlertCircle,
  FileText,
  TestTube,
  GitBranch,
  Activity,
  Scale,
  BookOpen,
  Sparkles,
  ArrowUpRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
} from "lucide-react";

export const Route = createFileRoute("/_app/repository-quality")({
  head: () => ({
    meta: [
      { title: "Repository Quality Analyzer — DevLink" },
      {
        name: "description",
        content:
          "Analyze GitHub repositories and generate an overall quality score with improvement suggestions.",
      },
    ],
  }),
  component: RepositoryQualityPage,
});

const METRIC_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  readme: FileText,
  documentation: BookOpen,
  license: Scale,
  test_coverage: TestTube,
  ci_cd: GitBranch,
  recent_activity: Activity,
  open_issues: AlertCircle,
};

function getGradeColor(grade: string): string {
  switch (grade) {
    case "A":
      return "text-emerald-500";
    case "B":
      return "text-blue-500";
    case "C":
      return "text-amber-500";
    case "D":
      return "text-orange-500";
    case "F":
      return "text-red-500";
    default:
      return "text-muted-foreground";
  }
}

function getScoreBarColor(score: number): string {
  if (score >= 0.8) return "bg-emerald-500";
  if (score >= 0.6) return "bg-blue-500";
  if (score >= 0.4) return "bg-amber-500";
  return "bg-red-500";
}

function getPriorityIcon(priority: string) {
  switch (priority) {
    case "high":
      return <XCircle className="h-4 w-4 text-red-500" />;
    case "medium":
      return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    case "low":
      return <CheckCircle2 className="h-4 w-4 text-blue-500" />;
    default:
      return null;
  }
}

function MetricCard({ metric, index }: { metric: MetricScore; index: number }) {
  const Icon = METRIC_ICONS[metric.metric] || FileText;
  const percentage = Math.round(metric.score * 100);

  return (
    <motion.div
      variants={cardEntrance}
      custom={index}
      className="rounded-2xl border border-border bg-card p-4 shadow-soft"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">{metric.label}</h3>
            <span className="text-xs font-bold text-muted-foreground">
              {Math.round(metric.weight * 100)}%
            </span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ duration: 0.8, delay: index * STAGGER_DELAY, ease: "easeOut" }}
              className={cn("h-full rounded-full", getScoreBarColor(metric.score))}
            />
          </div>
          <div className="mt-1.5 flex items-center justify-between">
            <p className="text-[11px] text-muted-foreground truncate pr-2">{metric.description}</p>
            <span className="text-xs font-bold tabular-nums">{percentage}%</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function SuggestionCard({
  suggestion,
  index,
}: {
  suggestion: ImprovementSuggestion;
  index: number;
}) {
  return (
    <motion.div
      variants={cardEntrance}
      custom={index}
      className="rounded-2xl border border-border bg-card p-4 shadow-soft"
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{getPriorityIcon(suggestion.priority)}</div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-foreground">{suggestion.title}</h4>
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
                suggestion.priority === "high" && "bg-red-500/10 text-red-500",
                suggestion.priority === "medium" && "bg-amber-500/10 text-amber-500",
                suggestion.priority === "low" && "bg-blue-500/10 text-blue-500"
              )}
            >
              {suggestion.priority}
            </span>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {suggestion.description}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function ResultDisplay({ result }: { result: RepositoryQualityResponse }) {
  const { repository_info } = result;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div
        variants={cardEntrance}
        className="rounded-3xl border border-border bg-card p-6 shadow-soft"
      >
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{result.owner}</span>
              <span>/</span>
              <span className="font-semibold text-foreground">{result.name}</span>
              <a
                href={result.repository_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center hover:text-primary transition-colors"
              >
                <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
            {repository_info.description && (
              <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                {repository_info.description}
              </p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Star className="h-3.5 w-3.5" />
                {repository_info.stars.toLocaleString()}
              </span>
              <span className="inline-flex items-center gap-1">
                <GitFork className="h-3.5 w-3.5" />
                {repository_info.forks.toLocaleString()}
              </span>
              <span className="inline-flex items-center gap-1">
                <AlertCircle className="h-3.5 w-3.5" />
                {repository_info.open_issues} issues
              </span>
              {repository_info.language && (
                <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
                  {repository_info.language}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-center sm:items-end">
            <div className="relative">
              <svg className="h-20 w-20 -rotate-90" viewBox="0 0 36 36">
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-muted/50"
                />
                <motion.circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeDasharray={`${result.overall_score * 100} 100`}
                  strokeLinecap="round"
                  initial={{ strokeDasharray: "0 100" }}
                  animate={{
                    strokeDasharray: `${result.overall_score * 100} 100`,
                  }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className={getGradeColor(result.grade)}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={cn("text-2xl font-black", getGradeColor(result.grade))}>
                  {result.grade}
                </span>
              </div>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {Math.round(result.overall_score * 100)}% overall
            </p>
          </div>
        </div>
      </motion.div>

      {/* Summary */}
      <motion.div
        variants={cardEntrance}
        className="rounded-3xl border border-border bg-card p-6 shadow-soft"
      >
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">AI Summary</h2>
        </div>
        <p className="text-sm leading-relaxed text-muted-foreground">{result.summary}</p>
      </motion.div>

      {/* Metrics */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-foreground">Metric Breakdown</h2>
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-3 sm:grid-cols-2"
        >
          {result.metrics.map((metric, i) => (
            <MetricCard key={metric.metric} metric={metric} index={i} />
          ))}
        </motion.div>
      </div>

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-foreground">Improvement Suggestions</h2>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid gap-3"
          >
            {result.suggestions.map((suggestion, i) => (
              <SuggestionCard key={i} suggestion={suggestion} index={i} />
            ))}
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

function RepositoryQualityPage() {
  const [url, setUrl] = useState("");

  const mutation = useMutation({
    mutationFn: (repositoryUrl: string) => repositoryQualityApi.analyze(repositoryUrl),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    mutation.mutate(url.trim());
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-black text-foreground sm:text-3xl">
          Repository Quality Analyzer
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Analyze any GitHub repository and get a comprehensive quality score with actionable
          improvement suggestions.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="h-11 w-full rounded-xl border border-border bg-card pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors"
              required
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending || !url.trim()}
            className="inline-flex h-11 items-center justify-center rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Analyze"}
          </button>
        </div>
      </form>

      {mutation.isError && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-500"
        >
          {mutation.error instanceof Error
            ? mutation.error.message
            : "Failed to analyze repository. Please check the URL and try again."}
        </motion.div>
      )}

      {mutation.data && <ResultDisplay result={mutation.data} />}

      {!mutation.data && !mutation.isPending && !mutation.isError && (
        <div className="rounded-3xl border border-dashed border-border bg-card/50 p-12 text-center">
          <Sparkles className="mx-auto h-10 w-10 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">
            Enter a GitHub repository URL above to analyze its quality.
          </p>
        </div>
      )}
    </div>
  );
}
