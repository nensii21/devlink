import { useQuery } from "@tanstack/react-query";
import { activitiesService } from "@/services";
import { Card, Skeleton } from "@/components/shared/primitives";
import { formatDistanceToNow } from "date-fns";
import { UserPlus, Edit3, FolderPlus, Award, Clock, MessageCircle, FileText, Github } from "lucide-react";
import type { BackendActivity } from "@/services";
import { TypoCaption } from "@/components/shared/Typography";

interface ActivityTimelineProps {
  userId: string;
}

function getActivityIcon(type: string) {
  switch (type) {
    case "user_registered":
      return <UserPlus className="h-4 w-4 text-primary" />;
    case "profile_updated":
      return <Edit3 className="h-4 w-4 text-emerald-500" />;
    case "project_created":
    case "project_joined":
      return <FolderPlus className="h-4 w-4 text-blue-500" />;
    case "badge_earned":
      return <Award className="h-4 w-4 text-amber-500" />;
    case "comment_created":
      return <MessageCircle className="h-4 w-4 text-indigo-500" />;
    case "builder_flare_created":
      return <FileText className="h-4 w-4 text-purple-500" />;
    case "repository_connected":
      return <Github className="h-4 w-4 text-gray-700" />;
    case "followed_user":
      return <UserPlus className="h-4 w-4 text-pink-500" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

export function ActivityTimeline({ userId }: ActivityTimelineProps) {
  const {
    data: activities,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["user-activities", userId],
    queryFn: () => activitiesService.user(userId),
  });

  return (
    <Card className="p-4 mt-4">
      <p className="text-[13px] font-semibold text-foreground mb-4">Activity Timeline</p>

      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-8 w-8 rounded-full shrink-0" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/4" />
              </div>
            </div>
          ))}
        </div>
      )}

      {isError && <p className="text-[13px] text-destructive">Failed to load recent activity.</p>}

      {!isLoading && !isError && activities?.length === 0 && (
        <TypoCaption as="p">No recent activity to show.</TypoCaption>
      )}

      {!isLoading && !isError && activities && activities.length > 0 && (
        <div className="relative border-l border-border ml-3 space-y-6">
          {activities.map((activity: BackendActivity) => (
            <div key={activity.id} className="relative pl-6">
              <span className="absolute -left-[17px] top-1 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-surface">
                {getActivityIcon(activity.activity_type)}
              </span>
              <div className="flex flex-col">
                <p className="text-[13px] font-medium text-foreground">{activity.title}</p>
                {activity.description && <TypoCaption as="p">{activity.description}</TypoCaption>}
                <time className="text-[11px] text-muted-foreground mt-1">
                  {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                </time>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
