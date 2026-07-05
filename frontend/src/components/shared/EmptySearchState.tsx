import { SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptySearchStateProps {
  /** The search query or filter descriptor to show in the message */
  query?: string;
  /** Override the default heading */
  title?: string;
  /** Override the default sub-text */
  description?: string;
  /** Label for the reset/clear button. If omitted, no button is rendered. */
  actionLabel?: string;
  /** Called when the user clicks the reset button */
  onReset?: () => void;
  /** Extra classes applied to the root wrapper */
  className?: string;
}

export function EmptySearchState({
  query,
  title,
  description,
  actionLabel = "Clear search",
  onReset,
  className,
}: EmptySearchStateProps) {
  const heading = title ?? (query ? `No results for "${query}"` : "No results found");
  const subtext =
    description ?? "Try adjusting your search or filters to find what you're looking for.";

  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center gap-4 px-4 py-12 text-center",
        "animate-in fade-in-50 duration-300",
        className,
      )}
    >
      {/* Icon container */}
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-muted text-muted-foreground">
        <SearchX size={28} strokeWidth={1.5} />
      </div>

      {/* Copy */}
      <div className="max-w-xs space-y-1.5">
        <p className="text-[15px] font-semibold tracking-tight text-foreground">{heading}</p>
        <p className="text-[13px] leading-relaxed text-muted-foreground">{subtext}</p>
      </div>

      {/* Optional reset action */}
      {onReset && (
        <Button variant="outline" size="sm" onClick={onReset}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
