import { cn } from "@/lib/utils";
import {
  getCollaborationStatusOption,
  type CollaborationStatus,
} from "@/features/collaboration/types";

interface CollaborationStatusBadgeProps {
  status?: CollaborationStatus | string | null;
  className?: string;
  showLabel?: boolean;
}

export function CollaborationStatusBadge({
  status,
  className,
  showLabel = true,
}: CollaborationStatusBadgeProps) {
  const option = getCollaborationStatusOption(status);
  const Icon = option.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        option.badgeClass,
        className,
      )}
      title={option.description}
    >
      <span className={cn("size-2 rounded-full", option.dotClass)} aria-hidden="true" />
      {showLabel && <span>{option.label}</span>}
      {!showLabel && <span className="sr-only">{option.label}</span>}
      <Icon className="size-3" aria-hidden="true" />
    </span>
  );
}
