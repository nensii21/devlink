import { createFileRoute } from "@tanstack/react-router";
import { ActivityFeed } from "@/features/activities/components/ActivityFeed";

export const Route = createFileRoute("/_app/feed")({
  component: FeedRoute,
});

function FeedRoute() {
  return (
    <div className="container mx-auto py-8 px-4 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Activity Feed</h1>
        <p className="text-gray-500 mt-2">
          Stay updated with everything happening across your projects and network.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <ActivityFeed />
      </div>
    </div>
  );
}
