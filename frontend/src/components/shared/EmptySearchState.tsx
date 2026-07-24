import { SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptySearchStateProps {
  title?: string;
  description?: string;
  onReset?: () => void;
  resetLabel?: string;
}

export function EmptySearchState({
  title = "No projects found.",
  description = "Try adjusting your search terms or filters.",
  onReset,
  resetLabel = "Clear filters",
}: EmptySearchStateProps) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center animate-in fade-in duration-200">
      <div className="mb-4 rounded-full bg-muted p-4">
        <SearchX className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="text-[14px] font-semibold text-foreground">{title}</p>
      <p className="mt-1 max-w-xs text-center text-[13px] text-muted-foreground">{description}</p>
      {onReset && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onReset}>
          {resetLabel}
        </Button>
      )}
    </div>
  );
}
