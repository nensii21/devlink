import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { analyticsApi, CommunityStatsResponse } from "@/api/modules/analytics";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/admin/community-stats")({
  component: CommunityStatsDashboard,
});

const CHART_COLORS = [
  "#2563eb",
  "#16a34a",
  "#ca8a04",
  "#dc2626",
  "#9333ea",
  "#0ea5e9",
  "#f97316",
  "#ec4899",
  "#14b8a6",
  "#6366f1",
];

function CommunityStatsDashboard() {
  const [data, setData] = useState<CommunityStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [days, setDays] = useState(30);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const res = await analyticsApi.communityStats(days);
      setData(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load data";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchData, 60_000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  if (loading) {
    return (
      <div className="p-6" role="status" aria-live="polite">
        <div className="flex items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          <span className="text-lg font-medium text-gray-700">Loading community statistics…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6" role="alert">
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          <p className="font-medium mb-2">Failed to load community statistics</p>
          <p className="text-sm mb-4">{error}</p>
          <button
            onClick={() => {
              setLoading(true);
              fetchData();
            }}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const formatNumber = (n: number) => new Intl.NumberFormat().format(n);

  const metricCards = [
    {
      title: "Total Developers",
      value: formatNumber(data.total_developers),
      color: "bg-blue-50 text-blue-700 border-blue-200",
      icon: "👥",
    },
    {
      title: "Active Projects",
      value: formatNumber(data.active_projects),
      color: "bg-green-50 text-green-700 border-green-200",
      icon: "🚀",
    },
    {
      title: "Teams Formed",
      value: formatNumber(data.teams_formed),
      color: "bg-purple-50 text-purple-700 border-purple-200",
      icon: "🤝",
    },
    {
      title: "Open Opportunities",
      value: formatNumber(data.open_opportunities),
      color: "bg-orange-50 text-orange-700 border-orange-200",
      icon: "💼",
    },
    {
      title: "Contributions This Month",
      value: formatNumber(data.contributions_this_month),
      color: "bg-teal-50 text-teal-700 border-teal-200",
      icon: "📈",
    },
    {
      title: "New Users This Month",
      value: formatNumber(data.new_users_this_month),
      color: "bg-indigo-50 text-indigo-700 border-indigo-200",
      icon: "✨",
    },
  ];

  return (
    <div className="p-6" role="main" aria-label="Community Statistics Dashboard">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <TypoHeading as="h1">Community Statistics Dashboard</TypoHeading>
          <TypoCaption as="p">
            Platform-wide metrics for the last {data.timeframe_days} days. Updated:{" "}
            {new Date(data.generated_at).toLocaleString()}
          </TypoCaption>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              aria-label="Enable auto-refresh every 60 seconds"
            />
            <span className="text-sm font-medium">Auto-refresh (60s)</span>
          </label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            aria-label="Timeframe in days"
          >
            <option value={7}>7 Days</option>
            <option value={30}>30 Days</option>
            <option value={90}>90 Days</option>
            <option value={180}>180 Days</option>
            <option value={365}>365 Days</option>
          </select>
        </div>
      </header>

      <section aria-labelledby="metrics-heading" className="mb-8">
        <h2 id="metrics-heading" className="sr-only">
          Key Metrics
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {metricCards.map((metric, idx) => (
            <article
              key={metric.title}
              className={`rounded-xl border p-5 ${metric.color} transition-shadow hover:shadow-md`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span aria-hidden="true" className="text-xl">
                  {metric.icon}
                </span>
                <TypoSection>{metric.title}</TypoSection>
              </div>
              <p className="text-3xl font-bold">{metric.value}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section aria-labelledby="skills-heading" className="bg-white rounded-xl border p-6">
          <h2 id="skills-heading" className="text-lg font-semibold mb-4">
            Most Popular Skills
          </h2>
          {data.most_popular_skills.length === 0 ? (
            <TypoCaption as="p">No skill data available.</TypoCaption>
          ) : (
            <div className="h-80" role="img" aria-label="Bar chart showing most popular skills">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.most_popular_skills}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 10, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [formatNumber(value), "Developers"]}
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={32}>
                    {data.most_popular_skills.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <table className="mt-4 w-full text-sm" role="table">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="p-3 text-left font-medium text-gray-500">Rank</th>
                <th className="p-3 text-left font-medium text-gray-500">Skill</th>
                <th className="p-3 text-right font-medium text-gray-500">Developers</th>
              </tr>
            </thead>
            <tbody>
              {data.most_popular_skills.map((skill, idx) => (
                <tr key={skill.name} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="p-3 text-gray-500">#{idx + 1}</td>
                  <td className="p-3 font-medium">{skill.name}</td>
                  <td className="p-3 text-right">{formatNumber(skill.count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section aria-labelledby="tech-heading" className="bg-white rounded-xl border p-6">
          <h2 id="tech-heading" className="text-lg font-semibold mb-4">
            Trending Technologies
          </h2>
          {data.trending_technologies.length === 0 ? (
            <TypoCaption as="p">No technology data available.</TypoCaption>
          ) : (
            <div className="h-80" role="img" aria-label="Bar chart showing trending technologies">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.trending_technologies}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 10, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => [formatNumber(value), "Projects"]}
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={32}>
                    {data.trending_technologies.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <table className="mt-4 w-full text-sm" role="table">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="p-3 text-left font-medium text-gray-500">Rank</th>
                <th className="p-3 text-left font-medium text-gray-500">Technology</th>
                <th className="p-3 text-right font-medium text-gray-500">Projects</th>
              </tr>
            </thead>
            <tbody>
              {data.trending_technologies.map((tech, idx) => (
                <tr key={tech.name} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="p-3 text-gray-500">#{idx + 1}</td>
                  <td className="p-3 font-medium">{tech.name}</td>
                  <td className="p-3 text-right">{formatNumber(tech.count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
