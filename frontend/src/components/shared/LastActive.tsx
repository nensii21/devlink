import { cn } from "@/lib/utils";
import { formatLastActive } from "@/lib/relative-time";
import { Clock } from "lucide-react";

export function LastActive({
  lastActiveAt,
  className,
}: {
  lastActiveAt: string | null | undefined;
  className?: string;
}) {
  const { label, exact } = formatLastActive(lastActiveAt);
  const isActive = label === "Active now";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-[12px]",
        isActive ? "text-success" : "text-muted-foreground",
        className,
      )}
      title={exact ?? undefined}
    >
      <Clock size={12} aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
