import { useCallback, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { activitiesApi, ActivityType } from "@/api/modules/activities";
import { ActivityItem } from "./ActivityItem";
import { Skeleton } from "@/components/ui/skeleton";
import { useIntersectionObserver } from "@/hooks/useIntersectionObserver";

type FilterGroup = {
  id: string;
  label: string;
  types: ActivityType[] | undefined;
};

const FILTERS: FilterGroup[] = [
  { id: "all", label: "All Activity", types: undefined },
  {
    id: "projects",
    label: "Projects",
    types: ["project_created", "project_updated", "project_archived", "project_milestone"],
  },
  {
    id: "applications",
    label: "Applications",
    types: ["application_submitted", "application_accepted", "application_rejected"],
  },
  { id: "followers", label: "Followers", types: ["followed_user"] },
  { id: "discussions", label: "Discussions", types: ["discussion_created", "comment_created"] },
  { id: "invitations", label: "Invitations", types: ["team_invitation"] },
  { id: "profile", label: "Profile Updates", types: ["profile_updated", "user_registered"] },
];

const PAGE_SIZE = 20;

interface ActivityFeedProps {
  actorId?: string;
  targetId?: string;
  targetType?: string;
}

function ActivitySkeleton() {
  return (
    <div className="flex gap-4 p-4 rounded-lg bg-white border border-gray-100">
      <Skeleton className="h-10 w-10 rounded-full shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export function ActivityFeed({ actorId, targetId, targetType }: ActivityFeedProps) {
  const [activeFilterId, setActiveFilterId] = useState<string>("all");

  const activeFilter = FILTERS.find((f) => f.id === activeFilterId);
  const activityTypes = activeFilter?.types;

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, status } = useInfiniteQuery({
    queryKey: ["activities", { actorId, targetId, targetType, activityTypes }],
    queryFn: async ({ pageParam }) => {
      const response = await activitiesApi.getFeed({
        limit: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        actor_id: actorId,
        target_id: targetId,
        target_type: targetType,
        activity_types: activityTypes,
      });
      return response;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => {
      if (!lastPage || lastPage.length < PAGE_SIZE) return undefined;
      return lastPage[lastPage.length - 1].created_at;
    },
  });

  const handleIntersect = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const sentinelRef = useIntersectionObserver(
    handleIntersect,
    Boolean(hasNextPage && !isFetchingNextPage),
  );

  const activities = data?.pages.flatMap((page) => page) ?? [];

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="flex flex-wrap gap-2 pb-2" role="group" aria-label="Activity filters">
        {FILTERS.map((filter) => (
          <button
            key={filter.id}
            onClick={() => setActiveFilterId(filter.id)}
            aria-pressed={activeFilterId === filter.id}
            className={`px-4 py-2 text-sm font-medium rounded-full transition-colors ${
              activeFilterId === filter.id
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="space-y-4" role="feed" aria-busy={status === "pending" || isFetchingNextPage}>
        {status === "pending" ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <ActivitySkeleton key={i} />
            ))}
          </div>
        ) : status === "error" ? (
          <div className="p-8 text-center bg-red-50 text-red-600 rounded-lg border border-red-100">
            <p>Failed to load activities. Please try again later.</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="p-12 text-center bg-gray-50 rounded-lg border border-gray-200 border-dashed">
            <p className="text-gray-500 font-medium">No activities found</p>
            <p className="text-sm text-gray-400 mt-1">Check back later or try a different filter.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}

            {isFetchingNextPage && (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <ActivitySkeleton key={i} />
                ))}
              </div>
            )}

            {hasNextPage && !isFetchingNextPage && (
              <div ref={sentinelRef} className="h-1" aria-hidden="true" />
            )}

            {!hasNextPage && activities.length > 0 && (
              <p className="py-4 text-center text-sm text-gray-400">
                You've reached the end of the feed.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
