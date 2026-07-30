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
      <svg
        width="120"
        height="100"
        viewBox="0 0 120 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="mb-4 animate-in zoom-in-50 duration-300"
      >
        <circle cx="50" cy="45" r="25" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" />
        <line x1="68" y1="63" x2="80" y2="75" stroke="var(--muted-foreground)" strokeWidth="3" opacity="0.2" strokeLinecap="round" />
        <line x1="42" y1="42" x2="58" y2="42" stroke="var(--primary)" strokeWidth="2" opacity="0.3" strokeLinecap="round" />
        <line x1="42" y1="50" x2="54" y2="50" stroke="var(--primary)" strokeWidth="2" opacity="0.2" strokeLinecap="round" />
        <circle cx="35" cy="25" r="3" fill="var(--primary)" opacity="0.15" />
      </svg>
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
