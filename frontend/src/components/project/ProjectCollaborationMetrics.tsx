import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  Clock,
  MessageSquare,
  CheckCircle2,
  Inbox,
  Activity,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Zap,
} from "lucide-react";
import {
  getProjectCollaborationMetrics,
  ProjectCollaborationMetricsResponse,
} from "../../api/modules/projectCollaborationMetrics";

interface Props {
  projectId: number;
}

export const ProjectCollaborationMetrics: React.FC<Props> = ({ projectId }) => {
  const [data, setData] = useState<ProjectCollaborationMetricsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProjectCollaborationMetrics(projectId);
      setData(res);
    } catch (err: unknown) {
      const errorObj = err as { message?: string };
      setError(errorObj?.message || "Failed to load collaboration metrics.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return (
    <div className="w-full max-w-5xl mx-auto p-6 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl space-y-6 text-slate-800 dark:text-slate-100 shadow-sm dark:shadow-none backdrop-blur-md transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />
            Project Collaboration Metrics
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Insights on team engagement, activity frequency, response velocity, and productivity.
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/60 rounded-lg text-cyan-700 dark:text-cyan-300 text-xs font-semibold">
            <Zap className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
            Health Score: {data.collaboration_score}/100
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-28 bg-slate-100 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/50 p-4 space-y-2"
            >
              <div className="h-4 bg-slate-200 dark:bg-slate-700/50 rounded w-1/2"></div>
              <div className="h-7 bg-slate-200 dark:bg-slate-700/50 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      )}

      {/* Error View */}
      {error && !loading && (
        <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/50 rounded-xl text-red-700 dark:text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
          <button
            onClick={fetchMetrics}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 dark:bg-red-800/50 dark:hover:bg-red-800 text-white text-xs font-medium rounded-lg border border-red-600 dark:border-red-700 flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      )}

      {/* Metrics Cards Grid */}
      {!loading && !error && data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Active Members
                </span>
                <div className="p-2 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-lg">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.active_members}
                </span>
                <span className="text-xs text-slate-500 ml-1.5">
                  / {data.total_team_size} total
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Avg Response Time
                </span>
                <div className="p-2 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-lg">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.avg_response_time_hours}
                </span>
                <span className="text-xs text-slate-500 ml-1.5">hours</span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Messages Exchanged
                </span>
                <div className="p-2 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-lg">
                  <MessageSquare className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.messages_exchanged}
                </span>
                <span className="text-xs text-emerald-600 dark:text-emerald-400 ml-2">
                  ↑ Active chat
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Tasks Completed
                </span>
                <div className="p-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-lg">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.tasks_completed}
                </span>
                <span className="text-xs text-slate-500 ml-1.5">milestones done</span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Applications Received
                </span>
                <div className="p-2 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-lg">
                  <Inbox className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {data.applications_received}
                </span>
                <span className="text-xs text-slate-500 ml-1.5">candidates</span>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 rounded-xl transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  Daily Velocity
                </span>
                <div className="p-2 bg-pink-500/10 text-pink-600 dark:text-pink-400 rounded-lg">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">High</span>
                <span className="text-xs text-emerald-600 dark:text-emerald-400 ml-2">
                  Top 5% speed
                </span>
              </div>
            </div>
          </div>

          <div className="p-5 bg-slate-50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800 rounded-xl space-y-3">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
              Daily Activity Breakdown (Last 7 Days)
            </h3>
            <div className="grid grid-cols-7 gap-2 pt-2">
              {data.daily_activity.map((pt, idx) => (
                <div key={idx} className="flex flex-col items-center gap-2">
                  <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-t-lg h-24 flex items-end p-1 justify-center relative group">
                    <div
                      className="w-full bg-cyan-500 group-hover:bg-cyan-400 rounded-t transition-all"
                      style={{ height: `${Math.min(100, pt.activity_count * 5)}%` }}
                    ></div>
                    <span className="absolute -top-6 text-[10px] bg-slate-800 text-slate-100 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      {pt.activity_count}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                    {pt.date.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
