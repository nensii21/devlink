import type { LucideIcon } from "lucide-react";
import { CircleCheck, Code2, GitPullRequest, Search, Video } from "lucide-react";

export type CollaborationStatus =
  "coding" | "reviewing_pr" | "in_meeting" | "looking_for_project" | "available";

export interface CollaborationStatusOption {
  value: CollaborationStatus;
  label: string;
  description: string;
  icon: LucideIcon;
  /** Tailwind classes for the status dot / badge accent. */
  dotClass: string;
  badgeClass: string;
}

export const COLLABORATION_STATUSES: CollaborationStatusOption[] = [
  {
    value: "coding",
    label: "Coding",
    description: "Currently writing code",
    icon: Code2,
    dotClass: "bg-violet-500",
    badgeClass: "text-violet-700 bg-violet-50 border-violet-200",
  },
  {
    value: "reviewing_pr",
    label: "Reviewing PR",
    description: "Reviewing pull requests",
    icon: GitPullRequest,
    dotClass: "bg-blue-500",
    badgeClass: "text-blue-700 bg-blue-50 border-blue-200",
  },
  {
    value: "in_meeting",
    label: "In meeting",
    description: "Currently in a meeting",
    icon: Video,
    dotClass: "bg-amber-500",
    badgeClass: "text-amber-700 bg-amber-50 border-amber-200",
  },
  {
    value: "looking_for_project",
    label: "Looking for project",
    description: "Open to joining a project",
    icon: Search,
    dotClass: "bg-emerald-500",
    badgeClass: "text-emerald-700 bg-emerald-50 border-emerald-200",
  },
  {
    value: "available",
    label: "Available now",
    description: "Ready to collaborate",
    icon: CircleCheck,
    dotClass: "bg-green-500",
    badgeClass: "text-green-700 bg-green-50 border-green-200",
  },
];

const STATUS_MAP = new Map(COLLABORATION_STATUSES.map((option) => [option.value, option]));

export function getCollaborationStatusOption(
  status: CollaborationStatus | string | null | undefined,
): CollaborationStatusOption {
  const option = status ? STATUS_MAP.get(status as CollaborationStatus) : undefined;
  return option ?? COLLABORATION_STATUSES[COLLABORATION_STATUSES.length - 1];
}
