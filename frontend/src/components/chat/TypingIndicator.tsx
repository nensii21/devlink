import { cn } from "@/lib/utils";

/**
 * TypingIndicator
 *
 * Animated three-dot "X is typing…" indicator shown in the chat thread
 * when another participant is typing. Issue #337.
 *
 * Props:
 *   label   - text shown next to the dots (e.g. "Alex is typing"). If
 *             omitted, only the dots are rendered.
 *   className - extra classes for the wrapper.
 */
export function TypingIndicator({ label, className }: { label?: string; className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 px-1 py-1 text-[12px] text-muted-foreground",
        className,
      )}
      aria-live="polite"
      role="status"
    >
      <span className="flex items-center gap-0.5">
        <Dot delay="0ms" />
        <Dot delay="150ms" />
        <Dot delay="300ms" />
      </span>
      {label && <span className="animate-pulse">{label}</span>}
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground/70 animate-bounce"
      style={{ animationDelay: delay, animationDuration: "1s" }}
    />
  );
}
