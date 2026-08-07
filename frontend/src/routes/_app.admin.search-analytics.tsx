import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import api from "@/lib/api";

export const Route = createFileRoute("/_app/admin/search-analytics")({
  component: SearchAnalyticsDashboard,
});

interface SearchAnalyticsData {
  total_searches: number;
  zero_result_rate_pct: number;
  click_through_rate_pct: number;
  average_latency_ms: number;
  top_keywords: { keyword: string; count: number }[];
}

function SearchAnalyticsDashboard() {
  const [data, setData] = useState<SearchAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      // Assuming api wrapper adds the base url and token
      setData(await api.get<SearchAnalyticsData>("/api/search/analytics?days=30"));
    } catch (error) {
      console.error("Failed to fetch search analytics", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-6">Loading Analytics...</div>;
  if (!data) return <div className="p-6 text-red-500">Failed to load data.</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Platform Search Analytics (Last 30 Days)</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded shadow border">
          <h3 className="text-gray-500 text-sm font-medium">Total Searches</h3>
          <p className="text-3xl font-bold mt-2">{data.total_searches}</p>
        </div>

        <div className="bg-white p-6 rounded shadow border">
          <h3 className="text-gray-500 text-sm font-medium">Zero-Result Rate</h3>
          <p className="text-3xl font-bold mt-2 text-rose-600">{data.zero_result_rate_pct}%</p>
        </div>

        <div className="bg-white p-6 rounded shadow border">
          <h3 className="text-gray-500 text-sm font-medium">Click-Through Rate (CTR)</h3>
          <p className="text-3xl font-bold mt-2 text-green-600">{data.click_through_rate_pct}%</p>
        </div>

        <div className="bg-white p-6 rounded shadow border">
          <h3 className="text-gray-500 text-sm font-medium">Avg Latency</h3>
          <p className="text-3xl font-bold mt-2 text-blue-600">{data.average_latency_ms} ms</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow border">
        <h2 className="text-xl font-semibold mb-4">Top 10 Searched Keywords</h2>
        {data.top_keywords?.length === 0 ? (
          <p className="text-gray-500">No keyword data available.</p>
        ) : (
          <table className="min-w-full text-left">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="p-3">Rank</th>
                <th className="p-3">Keyword</th>
                <th className="p-3">Search Count</th>
              </tr>
            </thead>
            <tbody>
              {data.top_keywords.map((item: { keyword: string; count: number }, idx: number) => (
                <tr key={idx} className="border-b">
                  <td className="p-3 text-gray-500">#{idx + 1}</td>
                  <td className="p-3 font-medium">{item?.keyword}</td>
                  <td className="p-3">{item?.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
