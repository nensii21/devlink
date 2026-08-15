import { createFileRoute } from "@tanstack/react-router";
import { GreetingHero } from "@/features/dashboard/GreetingHero";
import { StatsRow } from "@/features/dashboard/StatsRow";
import {
  CurrentProjects,
  AISuggestions,
  QuickActions,
  RecentActivity,
  Upcoming,
  NotificationsWidget,
  UpcomingEventsWidget,
  UpgradePlanCTA,
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
      {/* Main Grid Grouping (2-column layout on desktop) */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left/Main Column - 9 cols */}
        <div className="lg:col-span-9 flex flex-col gap-6">
          <div className="grid gap-6 md:grid-cols-2">
            <CurrentProjects />
            <AISuggestions />
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <QuickActions />
            <RecentActivity />
            <Upcoming />
          </div>
        </div>

        {/* Right Sidebar - 3 cols */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <NotificationsWidget />
          <UpcomingEventsWidget />
          <UpgradePlanCTA />
        </div>
      </div>
    </div>
  );
}
