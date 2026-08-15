import React, { useState, useEffect, useCallback } from "react";
import {
  UserPlus,
  UserMinus,
  ShieldCheck,
  Edit3,
  CheckCircle2,
  MessageSquare,
  FileUp,
  Clock,
  Filter,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { formatDistanceToNow, parseISO } from "date-fns";
import {
  getTeamActivityTimeline,
  TeamActivityItem,
  TeamActivityType,
} from "../../api/modules/teamActivity";

interface TeamActivityTimelineProps {
  projectId: number;
}

export const TeamActivityTimeline: React.FC<TeamActivityTimelineProps> = ({ projectId }) => {
  const [items, setItems] = useState<TeamActivityItem[]>([]);
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [selectedType, setSelectedType] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = useCallback(
    async (pageNum: number, typeFilter: string, isAppend: boolean = false) => {
      if (isAppend) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      setError(null);

      try {
        const res = await getTeamActivityTimeline(projectId, pageNum, 5, typeFilter || undefined);
        if (isAppend) {
          setItems((prev) => [...prev, ...res.items]);
        } else {
          setItems(res.items);
        }
        setHasMore(res.has_more);
      } catch (err: unknown) {
        const errorObj = err as { message?: string };
        setError(errorObj?.message || "Failed to load activity timeline.");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [projectId],
  );

  useEffect(() => {
    setPage(1);
    fetchTimeline(1, selectedType, false);
  }, [fetchTimeline, selectedType]);

  const handleLoadMore = () => {
    if (!hasMore || loadingMore) return;
    const nextPage = page + 1;
    setPage(nextPage);
    fetchTimeline(nextPage, selectedType, true);
  };

  const getActivityIcon = (type: TeamActivityType) => {
    switch (type) {
      case "member_joined":
        return <UserPlus className="w-5 h-5 text-emerald-400" />;
      case "member_left":
        return <UserMinus className="w-5 h-5 text-rose-400" />;
      case "role_updated":
        return <ShieldCheck className="w-5 h-5 text-amber-400" />;
      case "project_updated":
        return <Edit3 className="w-5 h-5 text-cyan-400" />;
      case "milestone_completed":
        return <CheckCircle2 className="w-5 h-5 text-cyan-400" />;
      case "new_discussion":
        return <MessageSquare className="w-5 h-5 text-purple-400" />;
      case "file_uploaded":
        return <FileUp className="w-5 h-5 text-cyan-400" />;
      default:
        return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };

  const formatRelativeTime = (dateStr: string) => {
    try {
      return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
    } catch {
      return dateStr;
    }
  };

  const filterOptions = [
    { label: "All Activities", value: "" },
    { label: "Member Joined", value: "member_joined" },
    { label: "Member Left", value: "member_left" },
    { label: "Role Updated", value: "role_updated" },
    { label: "Project Updated", value: "project_updated" },
    { label: "Milestone Completed", value: "milestone_completed" },
    { label: "New Discussion", value: "new_discussion" },
    { label: "File Uploaded", value: "file_uploaded" },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-slate-900/60 border border-slate-800 rounded-xl space-y-6 text-slate-100 backdrop-blur-md">
      {/* Header & Activity Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyan-400" />
            Team Activity Timeline
          </h3>
          <p className="text-xs text-slate-400">
            Real-time chronological activity stream for project team members.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-transparent text-xs font-medium text-slate-200 outline-none cursor-pointer"
          >
            {filterOptions.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-slate-800 text-slate-200">
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Initial Loading Skeleton */}
      {loading && (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex gap-4 animate-pulse">
              <div className="w-10 h-10 rounded-full bg-slate-800 shrink-0"></div>
              <div className="flex-1 space-y-2 py-1">
                <div className="h-4 bg-slate-800 rounded w-1/3"></div>
                <div className="h-3 bg-slate-800/60 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error View */}
      {error && !loading && (
        <div className="p-4 bg-red-950/40 border border-red-800/50 rounded-lg text-red-300 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Timeline Stream */}
      {!loading && !error && (
        <>
          {items.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl space-y-2">
              <Clock className="w-10 h-10 text-slate-600 mx-auto" />
              <p className="text-sm font-medium text-slate-400">No activity events found</p>
              <p className="text-xs text-slate-500">
                Activities will show up here as your team collaborates.
              </p>
            </div>
          ) : (
            <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {items.map((item) => (
                <div key={item.id} className="relative flex items-start gap-4 group">
                  <div className="absolute -left-6 top-0 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center shadow-sm">
                    {getActivityIcon(item.activity_type)}
                  </div>

                  <div className="flex-1 bg-slate-800/40 border border-slate-800 group-hover:border-slate-700 rounded-xl p-4 transition-all space-y-1.5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div className="flex items-center gap-2">
                        {item.actor_avatar && (
                          <img
                            src={item.actor_avatar}
                            alt={item.actor_name}
                            className="w-5 h-5 rounded-full bg-slate-700"
                          />
                        )}
                        <span className="text-xs font-semibold text-slate-300">
                          {item.actor_name}
                        </span>
                      </div>
                      <span className="text-[11px] font-medium text-cyan-400">
                        {formatRelativeTime(item.created_at)}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-white">{item.title}</h4>

                    {item.description && (
                      <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {hasMore && (
            <div className="text-center pt-4">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 inline-flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {loadingMore ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading...
                  </>
                ) : (
                  "Load More Activity"
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
