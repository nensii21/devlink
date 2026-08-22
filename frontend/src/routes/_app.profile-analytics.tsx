import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/shared/primitives";
import { analyticsApi } from "@/api/modules/analytics";
import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { TypoSection, TypoCaption, TypoCard, TypoHeading } from "@/components/shared/Typography";
import {
  Eye,
  Search,
  Users,
  Github,
  FolderGit2,
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Info,
  Calendar,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/_app/profile-analytics")({
  head: () => ({
    meta: [
      { title: "Profile Analytics — DevLink" },
      {
        name: "description",
        content: "Track your developer profile performance, views, search appearances, and clicks.",
      },
    ],
  }),
  component: ProfileAnalyticsPage,
});

function ProfileAnalyticsPage() {
  const [activeTab, setActiveTab] = useState<"all" | "views" | "search" | "connections" | "clicks">(
    "all",
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["profile-analytics"],
    queryFn: async () => {
      const response = await analyticsApi.profile();
      return response;
    },
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-[1536px] w-full p-6 space-y-6 animate-pulse">
        <div className="h-8 w-64 bg-muted rounded" />
        <div className="grid gap-6 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-28 bg-muted rounded-xl" />
          ))}
        </div>
        <div className="h-96 bg-muted rounded-xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-[1536px] w-full p-6 text-center space-y-4">
        <TypoHeading as="h2">Failed to load analytics</TypoHeading>
        <TypoCaption as="p">Please try again later.</TypoCaption>
        <Link to="/dashboard" className="text-xs text-primary hover:underline">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const { summary, trends } = data;

  const kpis = [
    {
      key: "profile_views",
      title: "Profile Views",
      value: summary.profile_views.total,
      growth: summary.profile_views.growth_pct,
      icon: <Eye className="h-5 w-5 text-indigo-500" />,
      color: "indigo",
      description: "Total page views of your developer profile",
    },
    {
      key: "search_appearances",
      title: "Search Appearances",
      value: summary.search_appearances.total,
      growth: summary.search_appearances.growth_pct,
      icon: <Search className="h-5 w-5 text-cyan-500" />,
      color: "cyan",
      description: "Appearances in developer & project search results",
    },
    {
      key: "connection_requests",
      title: "Connection Requests",
      value: summary.connection_requests.total,
      growth: summary.connection_requests.growth_pct,
      icon: <Users className="h-5 w-5 text-emerald-500" />,
      color: "emerald",
      description: "New developer followers and network connections",
    },
    {
      key: "repository_clicks",
      title: "Repository Clicks",
      value: summary.repository_clicks.total,
      growth: summary.repository_clicks.growth_pct,
      icon: <Github className="h-5 w-5 text-sky-500" />,
      color: "sky",
      description: "Clicks on your linked GitHub source repositories",
    },
    {
      key: "project_clicks",
      title: "Project Clicks",
      value: summary.project_clicks.total,
      growth: summary.project_clicks.growth_pct,
      icon: <FolderGit2 className="h-5 w-5 text-amber-500" />,
      color: "amber",
      description: "Clicks on your showcased portfolio project details",
    },
  ];

  return (
    <div className="mx-auto flex max-w-[1536px] w-full flex-col gap-6 pb-12 pt-4 px-4 sm:px-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
          >
            <ArrowLeft size={12} /> Back to Dashboard
          </Link>
          <TypoHeading as="h1">
            Professional Profile Analytics
            <Sparkles className="h-5 w-5 text-primary animate-pulse" />
          </TypoHeading>
          <TypoCaption as="p">
            Monitor views, search results, and developer click interactions.
          </TypoCaption>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-surface p-1 self-start sm:self-auto">
          <Calendar size={14} className="text-muted-foreground ml-2" />
          <span className="text-xs font-semibold text-foreground px-2">Last 7 Days</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {kpis.map((kpi) => {
          const isPositive = kpi.growth > 0;
          const isNegative = kpi.growth < 0;

          return (
            <Card
              key={kpi.key}
              className="p-5 flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden group border border-border"
            >
              {/* Background gradient effect on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="flex justify-between items-start">
                <div className="p-2 rounded-lg bg-muted/80">{kpi.icon}</div>
                <div
                  className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                    isPositive
                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                      : isNegative
                        ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isPositive && <TrendingUp size={11} />}
                  {isNegative && <TrendingDown size={11} />}
                  {kpi.growth > 0 ? `+${kpi.growth}` : kpi.growth}%
                </div>
              </div>

              <div className="mt-4 space-y-1 relative z-10">
                <TypoCaption as="p">{kpi.title}</TypoCaption>
                <TypoSection>{kpi.value}</TypoSection>
                <TypoCaption as="p">{kpi.description}</TypoCaption>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Trend Charts Section */}
      <Card className="p-6 border border-border space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
          <div className="space-y-1">
            <TypoSection>Performance Trends</TypoSection>
            <TypoCaption as="p">Analyze daily growth of your profile metrics.</TypoCaption>
          </div>

          {/* Filtering tabs */}
          <div className="flex flex-wrap gap-1 rounded-lg bg-muted p-1">
            {[
              { id: "all", label: "All Metrics" },
              { id: "views", label: "Views" },
              { id: "search", label: "Search" },
              { id: "connections", label: "Connections" },
              { id: "clicks", label: "Clicks" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                  activeTab === tab.id
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Recharts Chart */}
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorSearch" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorConnections" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorRepo" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorProj" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/40" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                className="text-[10px] fill-muted-foreground"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                className="text-[10px] fill-muted-foreground"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--background)",
                  borderColor: "var(--border)",
                  borderRadius: "8px",
                  fontSize: "11px",
                }}
                labelClassName="font-semibold text-foreground"
              />
              <Legend verticalAlign="top" height={36} className="text-xs" />

              {(activeTab === "all" || activeTab === "views") && (
                <Area
                  type="monotone"
                  dataKey="profile_views"
                  name="Profile Views"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorViews)"
                />
              )}
              {(activeTab === "all" || activeTab === "search") && (
                <Area
                  type="monotone"
                  dataKey="search_appearances"
                  name="Search Appearances"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorSearch)"
                />
              )}
              {(activeTab === "all" || activeTab === "connections") && (
                <Area
                  type="monotone"
                  dataKey="connection_requests"
                  name="Connection Requests"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorConnections)"
                />
              )}
              {(activeTab === "all" || activeTab === "clicks") && (
                <Area
                  type="monotone"
                  dataKey="repository_clicks"
                  name="Repository Clicks"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRepo)"
                />
              )}
              {(activeTab === "all" || activeTab === "clicks") && (
                <Area
                  type="monotone"
                  dataKey="project_clicks"
                  name="Project Clicks"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorProj)"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Info Warning Banner */}
      <Card className="p-4 bg-muted/40 border border-border/80 flex items-start gap-3">
        <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
        <div className="space-y-1">
          <TypoCard>About Profile Privacy & Analytics</TypoCard>
          <TypoCaption as="p">
            We respect developer privacy opt-outs. Visitor profiles are anonymous if the viewer has
            enabled private browsing in their settings. Clicks are logged anonymously, and search
            appearances are tallied for every global multi-category search index query match.
          </TypoCaption>
        </div>
      </Card>
    </div>
  );
}
