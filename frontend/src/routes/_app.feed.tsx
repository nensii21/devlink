import React, { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ActivityFeed } from "@/features/activities/components/ActivityFeed";
import { FeedComposer } from "@/features/activities/components/FeedComposer";
import { TrendingSidebar } from "@/features/activities/components/TrendingSidebar";
import { SuggestedBuildersSidebar } from "@/features/activities/components/SuggestedBuildersSidebar";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { Sparkles, Activity } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export const Route = createFileRoute("/_app/feed")({
  component: FeedRoute,
});

function FeedRoute() {
  const queryClient = useQueryClient();

  const handlePostCreated = () => {
    queryClient.invalidateQueries({ queryKey: ["activities"] });
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary mb-2">
          <Sparkles size={14} /> Builder Feed
        </div>
        <TypoHeading as="h1">Community & Activity Feed</TypoHeading>
        <TypoCaption as="p" className="mt-1 text-sm sm:text-base">
          Share updates, attach repositories, launch polls, and collaborate with builders across your network.
        </TypoCaption>
      </div>

      {/* Responsive Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Feed Column */}
        <div className="lg:col-span-8 space-y-6">
          {/* LinkedIn-style Builder Feed Composer (#943) */}
          <FeedComposer onPostCreated={handlePostCreated} />

          {/* Activity Feed Feed Items */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <ActivityFeed />
          </div>
        </div>

        {/* Right Sidebar Column */}
        <div className="lg:col-span-4 space-y-6 sticky top-20">
          {/* Trending Topics & Hashtags */}
          <TrendingSidebar />

          {/* Suggested Builders to Follow */}
          <SuggestedBuildersSidebar />
        </div>
      </div>
    </div>
  );
}

export default FeedRoute;
