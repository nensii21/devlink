import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { BarChart3, Download, Loader2 } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { analyticsApi, type RequestAnalytics } from "@/api/modules/analytics";
import { cn } from "@/lib/utils";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/admin/api-request-analytics")({
  component: ApiRequestAnalyticsDashboard,
});

const DAYS_OPTIONS = [7, 14, 30, 90];

function ApiRequestAnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<RequestAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await analyticsApi.requestAnalytics(days);
      setData(res);
    } catch (error) {
      console.error("Failed to fetch request analytics", error);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const exportCsv = async () => {
    try {
      const token = sessionStorage.getItem("devlink.access");
      const res = await fetch(`/api/analytics/requests/export?days=${days}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `request-analytics-${days}d.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <p className="text-destructive">Failed to load request analytics.</p>
      </div>
    );
  }

  const stats = [
    {
      label: "Total Requests",
      value: data.total_requests.toLocaleString(),
      accent: "text-foreground",
    },
    {
      label: "Avg Response Time",
      value: `${data.avg_response_time_ms} ms`,
      accent: "text-foreground",
    },
    {
      label: "Error Rate",
      value: `${data.error_rate_pct}%`,
      accent: data.error_rate_pct > 5 ? "text-destructive" : "text-success",
    },
    { label: "Active Users", value: data.active_users.toLocaleString(), accent: "text-foreground" },
    {
      label: "Rate-Limited",
      value: data.rate_limited_requests.toLocaleString(),
      accent: data.rate_limited_requests > 0 ? "text-warning" : "text-success",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <TypoHeading as="h2">API Request Analytics</TypoHeading>
          <TypoCaption as="p">
            Request volume, latency, and error tracking across the API.
          </TypoCaption>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-card p-1">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={cn(
                  "rounded-md px-3 py-1 text-[12px] font-medium transition-all",
                  days === d
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
                )}
              >
                {d}d
              </button>
            ))}
          </div>
          <button
            onClick={exportCsv}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[12px] font-medium text-muted-foreground transition-all hover:text-foreground hover:bg-accent/50"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {stats.map((s) => (
          <div key={s.label} className="rounded-2xl border border-border/60 bg-card p-5 shadow-sm">
            <TypoCaption as="p">{s.label}</TypoCaption>
            <p className={cn("mt-2 text-[28px] font-bold tracking-tight", s.accent)}>{s.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border/60 bg-card p-5 shadow-sm">
        <TypoSection>Daily Request Volume</TypoSection>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.daily_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" stroke="var(--color-muted-foreground)" fontSize={11} />
              <YAxis stroke="var(--color-muted-foreground)" fontSize={11} allowDecimals={false} />
              <Tooltip
                cursor={{ fill: "var(--color-muted)", opacity: 0.2 }}
                contentStyle={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar
                dataKey="requests"
                name="Requests"
                fill="var(--color-primary)"
                radius={[4, 4, 0, 0]}
              />
              <Bar dataKey="errors" name="Errors" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-2xl border border-border/60 bg-card p-5 shadow-sm">
        <TypoSection>Requests by Endpoint</TypoSection>
        {data.requests_by_endpoint.length === 0 ? (
          <TypoCaption as="p">No request data recorded yet.</TypoCaption>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr className="border-b border-border/40 text-[11px] uppercase tracking-wider text-muted-foreground">
                  <th className="p-3">Endpoint</th>
                  <th className="p-3">Method</th>
                  <th className="p-3 text-right">Requests</th>
                  <th className="p-3 text-right">Avg (ms)</th>
                  <th className="p-3 text-right">Errors</th>
                  <th className="p-3 text-right">Error Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {data.requests_by_endpoint.slice(0, 25).map((e) => (
                  <tr
                    key={`${e.method} ${e.endpoint}`}
                    className="transition-colors hover:bg-muted/20"
                  >
                    <td className="p-3 font-medium text-foreground">{e.endpoint}</td>
                    <td className="p-3">
                      <TypoCaption>{e.method}</TypoCaption>
                    </td>
                    <td className="p-3 text-right">{e.requests.toLocaleString()}</td>
                    <td className="p-3 text-right">{e.avg_response_time_ms}</td>
                    <td className="p-3 text-right">{e.error_count}</td>
                    <td
                      className={cn(
                        "p-3 text-right",
                        e.error_rate_pct > 5 ? "text-destructive" : "text-muted-foreground",
                      )}
                    >
                      {e.error_rate_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
