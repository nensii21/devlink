import { cn } from "@/lib/utils";
import type { ApplicationStatus } from "@/lib/api";

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  const className = cn(
    "inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
    status === "pending" && "bg-warning/10 text-warning border border-warning/30",
    status === "reviewing" && "bg-warning/10 text-warning border border-warning/30",
    status === "accepted" && "bg-success/10 text-success border border-success/30",
    status === "rejected" && "bg-destructive/10 text-destructive border border-destructive/30",
    status === "withdrawn" && "bg-destructive/10 text-destructive border border-destructive/30 opacity-70",
  );

  return <span className={className}>{status}</span>;
}

