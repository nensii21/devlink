import { createFileRoute } from "@tanstack/react-router";
import { GreetingHero } from "@/features/dashboard/GreetingHero";
import { StatsRow } from "@/features/dashboard/StatsRow";
import {
  RecentActivity,
  BuilderRequests,
  InviteRequests,
  SuggestedBuilders,
  TrendingProjects,
  AIRecommendations,
  MessagesPreview,
  QuickActions,
  UpcomingDeadlines,
  NotificationsFeed,
} from "@/features/dashboard/sections";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — DevLink" },
      {
        name: "description",
        content: "Your DevLink command center: projects, matches, messages and streaks.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="mx-auto flex max-w-[1536px] w-full flex-col gap-6 pb-12 pt-4 px-4 sm:px-6">
      <GreetingHero />

      <StatsRow />

      {/* Main Grid Grouping */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left/Main Column - 8 cols */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <SuggestedBuilders />
          <TrendingProjects />
          <div className="grid gap-6 sm:grid-cols-2">
            <BuilderRequests />
            <InviteRequests />
          </div>
          <div className="grid gap-6 sm:grid-cols-2">
            <MessagesPreview />
            <RecentActivity />
          </div>
        </div>

        {/* Right Sidebar - 4 cols */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <QuickActions />
          <AIRecommendations />
          <UpcomingDeadlines />
          <NotificationsFeed />
        </div>
      </div>
    </div>
  );
}
