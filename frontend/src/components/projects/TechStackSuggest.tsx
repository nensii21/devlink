import { useState } from "react";
import { Sparkles, Loader2, ChevronDown, ChevronUp, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { techStackService } from "@/services";
import type { TechStackRecommendation } from "@/api";

const CATEGORY_COLORS: Record<string, string> = {
  frontend: "bg-primary/10 text-primary border-primary/20",
  backend: "bg-info/10 text-info border-info/20",
  database: "bg-warning/10 text-warning border-warning/20",
  cache: "bg-success/10 text-success border-success/20",
  devops: "bg-muted text-muted-foreground border-border",
  testing: "bg-destructive/10 text-destructive border-destructive/20",
  auth: "bg-warning/10 text-warning border-warning/20",
  storage: "bg-info/10 text-info border-info/20",
};

interface TechStackSuggestProps {
  projectIdea: string;
  onSelect?: (techs: string[]) => void;
}

export function TechStackSuggest({ projectIdea, onSelect }: TechStackSuggestProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<TechStackRecommendation[]>([]);
  const [summary, setSummary] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (isOpen && recommendations.length > 0) {
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await techStackService.recommend(projectIdea);
      if (result && result.recommendations) {
        setRecommendations(result.recommendations);
        setSummary(result.summary ?? null);
        setIsOpen(true);
      } else {
        setError("No recommendations available. Try describing your project idea first.");
      }
    } catch {
      setError("Failed to get recommendations. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSelect = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const handleApplyAll = () => {
    const allNames = recommendations.map((r) => r.name);
    setSelected(new Set(allNames));
    onSelect?.(allNames);
  };

  const handleApplySelected = () => {
    onSelect?.(Array.from(selected));
  };

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={handleFetch}
        disabled={!projectIdea.trim() || isLoading}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-[12px] font-medium transition-colors",
          "border-primary/30 bg-primary/5 text-primary hover:bg-primary/10",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        )}
      >
        {isLoading ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <Sparkles size={13} />
        )}
        {isOpen ? "Hide suggestions" : "Get AI suggestion"}
      </button>

      {error && (
        <p className="text-[12px] text-destructive">{error}</p>
      )}

      {isOpen && recommendations.length > 0 && (
        <div className="rounded-md border border-border bg-surface p-3 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-[12px] font-semibold text-foreground">Recommended Stack</p>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleApplyAll}
                className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary hover:bg-primary/20"
              >
                Select all
              </button>
              {selected.size > 0 && (
                <button
                  type="button"
                  onClick={handleApplySelected}
                  className="rounded bg-primary px-2 py-0.5 text-[11px] font-medium text-primary-foreground hover:opacity-90"
                >
                  Apply ({selected.size})
                </button>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {recommendations.map((rec) => (
              <button
                key={rec.name}
                type="button"
                onClick={() => toggleSelect(rec.name)}
                className={cn(
                  "w-full rounded-md border p-2.5 text-left transition-colors",
                  selected.has(rec.name)
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50",
                )}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5">
                    <div
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded border",
                        selected.has(rec.name)
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border",
                      )}
                    >
                      {selected.has(rec.name) && <Check size={10} />}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-medium text-foreground">{rec.name}</span>
                      <span
                        className={cn(
                          "rounded border px-1.5 py-0.5 text-[10px] font-medium capitalize",
                          CATEGORY_COLORS[rec.category] ?? "bg-muted text-muted-foreground border-border",
                        )}
                      >
                        {rec.category}
                      </span>
                    </div>
                    <p className="mt-0.5 text-[12px] text-muted-foreground">{rec.reason}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {summary && (
            <p className="text-[12px] text-muted-foreground italic">{summary}</p>
          )}
        </div>
      )}
    </div>
  );
}
