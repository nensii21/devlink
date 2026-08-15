import React, { useState, useEffect, useCallback } from "react";
import {
  FolderPlus,
  Send,
  Eye,
  UserPlus,
  MessageSquare,
  Flame,
  Sparkles,
  TrendingUp,
  Calendar,
  AlertCircle,
  RefreshCw,
  Award,
} from "lucide-react";
import { getDeveloperInsights, DeveloperInsightsData } from "../../api/modules/developerInsights";

export const DeveloperInsightsDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState<string>("30d");
  const [data, setData] = useState<DeveloperInsightsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async (range: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDeveloperInsights(range);
      setData(res);
    } catch (err: unknown) {
      const errorObj = err as { message?: string };
      setError(errorObj?.message || "Failed to load developer insights.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInsights(dateRange);
  }, [dateRange, fetchInsights]);

  const ranges = [
    { label: "7 Days", value: "7d" },
    { label: "30 Days", value: "30d" },
    { label: "90 Days", value: "90d" },
    { label: "1 Year", value: "1y" },
    { label: "All Time", value: "all" },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 p-6 bg-white dark:bg-slate-900/60 text-slate-900 dark:text-slate-100 rounded-2xl border border-slate-200 dark:border-slate-800 backdrop-blur-md shadow-sm dark:shadow-none transition-colors">
      {/* Header & Date Range Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2.5 text-slate-900 dark:text-white">
            <Sparkles className="w-6 h-6 text-cyan-500 dark:text-cyan-400" />
            Developer Insights Dashboard
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Personalized summary of your activity, engagement metrics, and AI match performance on
            DevLink.
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1.5 rounded-xl border border-slate-200 dark:border-slate-700/80">
          <Calendar className="w-4 h-4 text-slate-400 ml-2 hidden sm:inline-block" />
          {ranges.map((r) => (
            <button
              key={r.value}
              onClick={() => setDateRange(r.value)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                dateRange === r.value
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/60"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="h-32 bg-slate-100 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/50 p-4 space-y-3"
            >
              <div className="h-4 bg-slate-200 dark:bg-slate-700/50 rounded w-1/2"></div>
              <div className="h-8 bg-slate-200 dark:bg-slate-700/50 rounded w-3/4"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700/50 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="p-6 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/50 rounded-xl text-red-700 dark:text-red-300 flex flex-col items-center gap-3 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 dark:text-red-400" />
          <p className="font-semibold text-base">{error}</p>
          <button
            onClick={() => fetchInsights(dateRange)}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 dark:bg-red-800/60 text-white text-xs font-semibold rounded-lg border border-red-500 transition-colors"
          >
            <RefreshCw className="w-4 h-4" /> Try Again
          </button>
        </div>
      )}

      {/* Main Content */}
      {!loading && !error && data && (
        <div className="space-y-6">
          {Object.values(data.metrics).every((val) => val === 0) ? (
            <div className="p-12 text-center bg-slate-50 dark:bg-slate-800/20 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
              <Sparkles className="w-12 h-12 text-slate-400 dark:text-slate-500 mx-auto" />
              <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300">
                No Activity Recorded
              </h3>
              <p className="text-sm text-slate-500">
                You haven't recorded any metrics for this date range yet.
              </p>
            </div>
          ) : (
            <>
              {/* Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Projects Created
                    </span>
                    <div className="p-2.5 bg-cyan-500/10 text-cyan-500 dark:text-cyan-400 rounded-xl group-hover:scale-105 transition-transform">
                      <FolderPlus className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.projects_created}
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>
                        +{data.trends.projects_created?.percentage_change}% vs prev period
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Applications Submitted
                    </span>
                    <div className="p-2.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-xl group-hover:scale-105 transition-transform">
                      <Send className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.applications_submitted}
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>
                        +{data.trends.applications_submitted?.percentage_change}% vs prev period
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Profile Views
                    </span>
                    <div className="p-2.5 bg-cyan-500/10 text-cyan-500 dark:text-cyan-400 rounded-xl group-hover:scale-105 transition-transform">
                      <Eye className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.profile_views}
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>+{data.trends.profile_views?.percentage_change}% vs prev period</span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Followers Gained
                    </span>
                    <div className="p-2.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-xl group-hover:scale-105 transition-transform">
                      <UserPlus className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.followers_gained}
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>
                        +{data.trends.followers_gained?.percentage_change}% vs prev period
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Messages Sent
                    </span>
                    <div className="p-2.5 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl group-hover:scale-105 transition-transform">
                      <MessageSquare className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.messages_sent}
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>+{data.trends.messages_sent?.percentage_change}% vs prev period</span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Contribution Streak
                    </span>
                    <div className="p-2.5 bg-orange-500/10 text-orange-600 dark:text-orange-400 rounded-xl group-hover:scale-105 transition-transform">
                      <Flame className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.contribution_streak} days
                    </span>
                    <div className="flex items-center gap-1 mt-1 text-xs text-orange-600 dark:text-orange-400 font-semibold">
                      <span>Active Streak 🔥</span>
                    </div>
                  </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-cyan-500/40 transition-all group sm:col-span-2 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      AI Match Success Rate
                    </span>
                    <div className="p-2.5 bg-cyan-500/10 text-cyan-500 dark:text-cyan-400 rounded-xl group-hover:scale-105 transition-transform">
                      <Award className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">
                      {data.metrics.ai_match_success_rate}%
                    </span>
                    <span className="text-xs text-cyan-600 dark:text-cyan-400 font-semibold">
                      High Skill Vector Fit
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700/80 h-2.5 rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-500 dark:bg-cyan-400 h-full rounded-full transition-all duration-500"
                      style={{ width: `${data.metrics.ai_match_success_rate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
