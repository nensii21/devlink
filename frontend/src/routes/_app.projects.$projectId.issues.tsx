import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { issuesService } from "@/services";
import { issuesApi } from "@/api";
import type { Issue } from "@/api";
import { Card } from "@/components/shared/primitives";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Copy,
  FileText,
  Filter,
  GitBranch,
  Plus,
  Search,
  Tag,
  X,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/projects/$projectId/issues")({
  head: () => ({
    meta: [
      { title: "Issues — DevLink" },
      { name: "description", content: "Manage project issues with AI duplicate detection." },
    ],
  }),
  component: IssuesPage,
});

const STATUS_CONFIG = {
  open: { icon: AlertCircle, color: "text-blue-500", bg: "bg-blue-500/10", label: "Open" },
  in_progress: {
    icon: Clock,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    label: "In Progress",
  },
  closed: { icon: CheckCircle2, color: "text-green-500", bg: "bg-green-500/10", label: "Closed" },
  duplicate: { icon: Copy, color: "text-purple-500", bg: "bg-purple-500/10", label: "Duplicate" },
} as const;

const PRIORITY_CONFIG = {
  low: { color: "text-muted-foreground", label: "Low" },
  medium: { color: "text-blue-500", label: "Medium" },
  high: { color: "text-amber-500", label: "High" },
  critical: { color: "text-red-500", label: "Critical" },
} as const;

function IssuesPage() {
  const { projectId } = Route.useParams();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDuplicateCheck, setShowDuplicateCheck] = useState(false);

  const { data: issues = [], isLoading } = useQuery({
    queryKey: ["issues", projectId],
    queryFn: () => issuesService.list(projectId),
  });

  const filteredIssues = issues.filter((issue: Issue) => {
    if (statusFilter !== "all" && issue.status !== statusFilter) return false;
    if (searchQuery && !issue.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">Issues</h1>
          <p className="text-[13px] text-muted-foreground">
            Track bugs, feature requests, and tasks with AI-powered duplicate detection.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowDuplicateCheck(true)}
            className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[13px] font-semibold hover:bg-muted"
          >
            <GitBranch size={14} /> Check Duplicates
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
          >
            <Plus size={14} /> New Issue
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <Card className="p-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search issues..."
              className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
            {(["all", "open", "in_progress", "closed", "duplicate"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={cn(
                  "rounded px-2.5 py-1 text-[12px] font-medium capitalize transition-colors",
                  statusFilter === f
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {f === "all" ? "All" : STATUS_CONFIG[f].label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Issues List */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="h-20 animate-pulse" />
          ))}
        </div>
      ) : filteredIssues.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
            <FileText size={20} />
          </div>
          <p className="text-[14px] font-semibold text-foreground">No issues found</p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            {searchQuery ? "Try adjusting your search." : "Create your first issue to get started."}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredIssues.map((issue: Issue) => {
            const statusConfig = STATUS_CONFIG[issue.status];
            const StatusIcon = statusConfig.icon;
            const priorityConfig = PRIORITY_CONFIG[issue.priority];

            return (
              <Card key={issue.id} interactive className="p-4">
                <div className="flex items-start gap-3">
                  <div className={cn("mt-0.5 rounded-full p-1.5", statusConfig.bg)}>
                    <StatusIcon size={14} className={statusConfig.color} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-[14px] font-semibold text-foreground truncate">
                        {issue.title}
                      </h3>
                      <span
                        className={cn(
                          "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                          statusConfig.bg,
                          statusConfig.color,
                        )}
                      >
                        {statusConfig.label}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-[12px] text-muted-foreground">
                      {issue.description}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                      <span className={cn("font-medium", priorityConfig.color)}>
                        {priorityConfig.label} Priority
                      </span>
                      {issue.labels && (
                        <span className="inline-flex items-center gap-1">
                          <Tag size={10} />
                          {issue.labels}
                        </span>
                      )}
                      <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Duplicate Check Modal */}
      {showDuplicateCheck && (
        <DuplicateCheckModal projectId={projectId} onClose={() => setShowDuplicateCheck(false)} />
      )}

      {/* Create Issue Modal */}
      {showCreateModal && (
        <CreateIssueModal projectId={projectId} onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

function DuplicateCheckModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [threshold, setThreshold] = useState(0.75);
  const [isChecking, setIsChecking] = useState(false);
  const [results, setResults] = useState<{
    has_duplicates: boolean;
    suggestions: Array<{
      id: string;
      similarity_score: number;
      issue?: { id: string; title: string; status: string };
    }>;
  } | null>(null);

  const handleCheck = async () => {
    if (!title.trim() || !description.trim()) return;
    setIsChecking(true);
    try {
      const result = await issuesApi.checkDuplicates(projectId, {
        title,
        description,
        threshold,
      });
      setResults(result);
    } catch (err) {
      console.error("Duplicate check failed:", err);
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-lg p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-[16px] font-bold text-foreground">Check for Duplicates</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Use AI to detect similar issues before creating a new one.
        </p>

        <div className="mt-4 space-y-3">
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Title
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Issue title..."
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the issue..."
              rows={4}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Similarity Threshold: {threshold}
            </label>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>More results</span>
              <span>More precise</span>
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-border px-3 py-2 text-[13px] font-medium hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={handleCheck}
            disabled={isChecking || !title.trim() || !description.trim()}
            className="rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {isChecking ? "Checking..." : "Check for Duplicates"}
          </button>
        </div>

        {/* Results */}
        {results && (
          <div className="mt-4 border-t border-border pt-4">
            {results.has_duplicates ? (
              <div>
                <p className="text-[13px] font-semibold text-amber-600">
                  Found {results.suggestions.length} similar issue(s)
                </p>
                <div className="mt-2 space-y-2">
                  {results.suggestions.map((suggestion) => (
                    <div
                      key={suggestion.id}
                      className="rounded-md border border-amber-200 bg-amber-50 p-3"
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-[13px] font-medium text-foreground">
                          {suggestion.issue?.title ?? "Unknown issue"}
                        </p>
                        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">
                          {Math.round(suggestion.similarity_score * 100)}% match
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle2 size={16} />
                <p className="text-[13px] font-medium">
                  No similar issues found. You're good to go!
                </p>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

function CreateIssueModal({ projectId, onClose }: { projectId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "critical">("medium");
  const [labels, setLabels] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const createMutation = useMutation({
    mutationFn: () =>
      issuesApi.create(projectId, {
        title,
        description,
        priority,
        labels: labels || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues", projectId] });
      onClose();
    },
  });

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) return;
    setIsSubmitting(true);
    try {
      await createMutation.mutateAsync();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-lg p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-[16px] font-bold text-foreground">Create Issue</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Title
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Issue title..."
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the issue..."
              rows={4}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as typeof priority)}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                Labels
              </label>
              <input
                value={labels}
                onChange={(e) => setLabels(e.target.value)}
                placeholder="bug, feature..."
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary"
              />
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-border px-3 py-2 text-[13px] font-medium hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !description.trim()}
            className="rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? "Creating..." : "Create Issue"}
          </button>
        </div>
      </Card>
    </div>
  );
}
