import {DashboardLayout} from "../components/layout/DashboardLayout";
import StatsCards from "../components/dashboard/StatsCards";
import RecentActivity from "../components/dashboard/RecentActivity";
import RecentApplications from "../components/dashboard/RecentApplications";

export default function Dashboard() {
  return (
    <DashboardLayout>
      <div className="space-y-8">

        <div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            Welcome back, Nancy
          </h1>

          <p className="mt-2 text-lg text-slate-500">
            Continue building with your team.
          </p>
        </div>

        <StatsCards />

        <div className="grid gap-8 xl:grid-cols-[2fr_1fr]">
          <RecentActivity />
          <RecentApplications />
        </div>

      </div>
    </DashboardLayout>
  );
}