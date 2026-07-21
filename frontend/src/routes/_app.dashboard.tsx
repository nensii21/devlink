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
    <div className="space-y-4">
      <GreetingHero />
      <StatsRow />
      <div className="grid gap-3 lg:grid-cols-3">
        <RecentActivity />
        <BuilderRequests />
        <InviteRequests />
      </div>
      <div className="grid gap-3 lg:grid-cols-[2fr_2fr_1.2fr]">
        <SuggestedBuilders />
        <TrendingProjects />
        <AIRecommendations />
      </div>
      <div className="grid gap-3 lg:grid-cols-4">
        <MessagesPreview />
        <QuickActions />
        <UpcomingDeadlines />
        <NotificationsFeed />
      </div>
    </div>
  );
}
