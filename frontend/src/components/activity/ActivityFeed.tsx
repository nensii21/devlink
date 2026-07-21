import { EmptyState, SectionHeader, Skeleton } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import type { BackendActivity } from "@/services";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import {
  Activity as ActivityIcon,
  Archive,
  Building2,
  FolderPlus,
  GitBranch,
  Pencil,
  UserPlus,
  UserRoundPen,
  type LucideIcon,
} from "lucide-react";

const activityIcons: Record<string, LucideIcon> = {
  "archive": Archive,
  "building-2": Building2,
  "folder-plus": FolderPlus,
  "git-branch": GitBranch,
  "pencil": Pencil,
  "user-plus": UserPlus,
  "user-round-pen": UserRoundPen,
};

const colorClasses: Record<string, string> = {
  info: "bg-info/10 text-info",
  primary: "bg-primary-soft text-primary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
};

function getActivityTime(createdAt: string) {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return formatDistanceToNow(date, { addSuffix: true });
}

function getActorName(activity: BackendActivity) {
  if (!activity.actor) {
    return null;
  }

  return `${activity.actor.first_name} ${activity.actor.last_name}`;
}

export function ActivityItem({ activity }: { activity: BackendActivity }) {
  const Icon = activity.icon ? activityIcons[activity.icon] ?? ActivityIcon : ActivityIcon;
  const actorName = getActorName(activity);

  return (
    <li className="flex items-start gap-3 px-4 py-2.5">
      <span
        className={cn(
          "mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-md",
          activity.color ? colorClasses[activity.color] : colorClasses.primary,
        )}
      >
        <Icon size={13} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-semibold text-foreground">{activity.title}</p>
        <p className="truncate text-[12px] text-muted-foreground">
          {activity.description ?? activity.activity_type.replaceAll("_", " ")}
          {actorName && <span> by {actorName}</span>}
        </p>
      </div>
      <span className="whitespace-nowrap text-[11px] text-muted-foreground">
        {getActivityTime(activity.created_at)}
      </span>
    </li>
  );
}

function ActivityFeedSkeleton() {
  return (
    <div className="space-y-3 px-4 pb-4">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex items-center gap-3">
          <Skeleton className="h-7 w-7 shrink-0" />
          <div className="min-w-0 flex-1 space-y-1.5">
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-3 w-12" />
        </div>
      ))}
    </div>
  );
}

export function ActivityFeed({
  queryKey,
  queryFn,
}: {
  queryKey: readonly unknown[];
  queryFn: () => Promise<BackendActivity[]>;
}) {
  const { data = [], isError, isLoading, refetch } = useQuery({
    queryKey,
    queryFn,
  });

  return (
    <>
      <SectionHeader title="Recent Activity" />
      {isLoading && <ActivityFeedSkeleton />}
      {isError && (
        <div className="px-4 pb-4">
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3">
            <p className="text-[13px] font-semibold text-foreground">Activity could not be loaded.</p>
            <button
              className="mt-1 text-[12px] font-medium text-primary hover:underline"
              onClick={() => void refetch()}
            >
              Try again
            </button>
          </div>
        </div>
      )}
      {!isLoading && !isError && data.length === 0 && (
        <EmptyState
          title="No activity yet"
          desc="Recent profile, project, repository, and follow updates will appear here."
        />
      )}
      {!isLoading && !isError && data.length > 0 && (
        <ul className="divide-y divide-border">
          {data.map((activity) => (
            <ActivityItem key={activity.id} activity={activity} />
          ))}
        </ul>
      )}
    </>
  );
}
