import { memo } from "react";
import { highlightMatches } from "@/lib/highlight";
import { cn } from "@/lib/utils";

interface HighlightTextProps {
  text: string;
  query: string;
  className?: string;
}

function HighlightTextInner({ text, query, className }: HighlightTextProps) {
  const segments = highlightMatches(text, query);

  return (
    <span className={cn(className)}>
      {segments.map((seg, i) =>
        seg.highlighted ? (
          <mark
            key={i}
            className="rounded-sm bg-warning/20 px-0.5 text-warning-foreground ring-1 ring-warning/30 dark:bg-warning/25 dark:text-warning dark:ring-warning/40"
          >
            {seg.text}
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </span>
  );
}

export const HighlightText = memo(HighlightTextInner);
