import React, { useState, useEffect, useRef, useCallback } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { activitiesApi, ActivityType } from "@/api/modules/activities";
import { ActivityItem } from "./ActivityItem";
import { Loader2 } from "lucide-react";

type FilterGroup = {
  id: string;
  label: string;
  types: ActivityType[] | undefined;
};

const FILTERS: FilterGroup[] = [
  { id: "all", label: "All Activity", types: undefined },
  { id: "projects", label: "Projects", types: ["project_created", "project_updated", "project_archived", "project_milestone"] },
  { id: "applications", label: "Applications", types: ["application_submitted", "application_accepted", "application_rejected"] },
  { id: "followers", label: "Followers", types: ["followed_user"] },
  { id: "discussions", label: "Discussions", types: ["discussion_created", "comment_created"] },
  { id: "invitations", label: "Invitations", types: ["team_invitation"] },
  { id: "profile", label: "Profile Updates", types: ["profile_updated", "user_registered"] },
];

interface ActivityFeedProps {
  actorId?: string;
  targetId?: string;
  targetType?: string;
}

export function ActivityFeed({ actorId, targetId, targetType }: ActivityFeedProps) {
  const [activeFilterId, setActiveFilterId] = useState<string>("all");
  
  const activeFilter = FILTERS.find(f => f.id === activeFilterId);
  const activityTypes = activeFilter?.types;

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ["activities", { actorId, targetId, targetType, activityTypes }],
    queryFn: async ({ pageParam }) => {
      const response = await activitiesApi.getFeed({
        limit: 20,
        cursor: pageParam as string | undefined,
        actor_id: actorId,
        target_id: targetId,
        target_type: targetType,
        activity_types: activityTypes,
      });
      return response.data;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => {
      if (!lastPage || lastPage.length < 20) return undefined;
      return lastPage[lastPage.length - 1].created_at;
    },
  });

  const observer = useRef<IntersectionObserver | null>(null);
  const lastElementRef = useCallback((node: HTMLDivElement | null) => {
    if (isFetchingNextPage) return;
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasNextPage) {
        fetchNextPage();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [isFetchingNextPage, hasNextPage, fetchNextPage]);

  const activities = data?.pages.flatMap(page => page) || [];

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      {/* Filters */}
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

      {/* Feed */}
      <div className="space-y-4" role="feed" aria-busy={status === "pending" || isFetchingNextPage}>
        {status === "pending" ? (
          <div className="flex justify-center p-8">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" aria-label="Loading activities" />
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
            {activities.map((activity, index) => {
              const isLast = index === activities.length - 1;
              return (
                <div key={activity.id} ref={isLast ? lastElementRef : null}>
                  <ActivityItem activity={activity} />
                </div>
              );
            })}
            
            {isFetchingNextPage && (
              <div className="flex justify-center p-4">
                <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
