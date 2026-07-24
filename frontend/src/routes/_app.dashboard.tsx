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
    <div className="space-y-5">
      <GreetingHero />
      <StatsRow />

      {/* Modern Bento Command Grid */}
      <div className="grid gap-5 lg:grid-cols-[1.8fr_1fr]">
        {/* Main Column */}
        <div className="space-y-5">
          <SuggestedBuilders />
          <TrendingProjects />
          <div className="grid gap-5 sm:grid-cols-2">
            <BuilderRequests />
            <InviteRequests />
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <MessagesPreview />
            <NotificationsFeed />
          </div>
        </div>

        {/* Side Column */}
        <div className="space-y-5">
          <QuickActions />
          <AIRecommendations />
          <UpcomingDeadlines />
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}
