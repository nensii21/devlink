import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ChevronUp,
  ChevronDown,
  RefreshCw,
  Activity,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Cpu,
  Search,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { api } from "@/api/client";

export const Route = createFileRoute("/_app/admin/jobs")({
  component: AdminJobsPage,
});

interface AdminJobStats {
  total: number;
  running: number;
  completed: number;
  failed: number;
  avg_processing_time?: number | null;
  worker_health?: {
    status: string;
    workers?: Record<
      string,
      { status: string; active_tasks: number; queued_tasks: number; total_processed: number }
    >;
  };
}

interface AdminJob {
  id: string;
  task_name: string;
  status: string;
  worker?: string | null;
  retries: number;
  processing_time: number | null;
  created_at: string;
  payload?: unknown;
  result?: unknown;
  error?: unknown;
}

interface AdminJobsResponse {
  total: number;
  jobs: AdminJob[];
}

function AdminJobsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const limit = 10;

  // Fetch stats and worker health every 5 seconds
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-job-stats"],
    queryFn: async () => {
      return api.get<AdminJobStats>("/admin/background-jobs/stats");
    },
    refetchInterval: 5000,
  });

  // Fetch jobs list
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["admin-jobs", statusFilter, search, page],
    queryFn: async () => {
      const params: {
        skip: number;
        limit: number;
        status?: string;
        search?: string;
      } = {
        skip: (page - 1) * limit,
        limit: limit,
      };
      if (statusFilter !== "all") params.status = statusFilter;
      if (search) params.search = search;

      return api.get<AdminJobsResponse>("/admin/background-jobs/", { query: params });
    },
  });

  const retryMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/admin/background-jobs/${id}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-job-stats"] });
      queryClient.invalidateQueries({ queryKey: ["admin-jobs"] });
    },
  });

  const toggleExpand = (id: string) => {
    if (expandedJobId === id) {
      setExpandedJobId(null);
    } else {
      setExpandedJobId(id);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return (
          <Badge className="bg-blue-500 hover:bg-blue-600 text-white animate-pulse">Running</Badge>
        );
      case "completed":
        return <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white">Completed</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "retry":
        return <Badge className="bg-amber-500 hover:bg-amber-600 text-white">Retrying</Badge>;
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  const formatTime = (seconds: number | null) => {
    if (seconds === null) return "-";
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const totalPages = jobsData ? Math.ceil(jobsData.total / limit) : 1;

  if (statsLoading)
    return (
      <div className="flex justify-center p-8">
        <RefreshCw className="animate-spin text-primary h-8 w-8" />
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Background Job Monitoring</h2>
        <p className="text-muted-foreground">
          Monitor asynchronous tasks, track worker health, and retry failed operations.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Play className="h-4 w-4 text-blue-500 animate-spin" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">{stats?.running || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">{stats?.completed || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{stats?.failed || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Process Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.avg_processing_time ? `${stats.avg_processing_time}s` : "-"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Worker Health */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader className="pb-3">
          <CardTitle className="text-md font-bold flex items-center gap-2">
            <Cpu className="h-5 w-5 text-primary" />
            Worker Cluster Health:
            <Badge
              className={
                stats?.worker_health?.status === "healthy"
                  ? "bg-emerald-500 text-white"
                  : "bg-amber-500 text-white"
              }
            >
              {stats?.worker_health?.status === "healthy" ? "Healthy" : "No Workers Detected"}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats?.worker_health?.workers && Object.keys(stats.worker_health.workers).length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mt-2">
              {Object.entries(
                stats.worker_health.workers as Record<
                  string,
                  {
                    status: string;
                    active_tasks: number;
                    queued_tasks: number;
                    total_processed: number;
                  }
                >,
              ).map(([name, info]) => (
                <div
                  key={name}
                  className="border border-border rounded-lg p-3 bg-surface/50 space-y-2"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm truncate max-w-[200px]" title={name}>
                      {name}
                    </span>
                    <Badge variant={info.status === "active" ? "default" : "secondary"}>
                      {info.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                    <div>
                      <p className="font-medium text-foreground">{info.active_tasks}</p>
                      <p>Active</p>
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{info.queued_tasks}</p>
                      <p>Queued</p>
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{info.total_processed}</p>
                      <p>Processed</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No active worker instances reporting heartbeat metrics.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Filters and Table */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-card p-4 rounded-lg border border-border">
          <div className="flex flex-1 w-full max-w-md items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search jobs by ID, name, or payload..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Select
              value={statusFilter}
              onValueChange={(val) => {
                setStatusFilter(val);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="retry">Retrying</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {jobsLoading ? (
          <div className="flex justify-center p-8">
            <RefreshCw className="animate-spin text-primary h-8 w-8" />
          </div>
        ) : !jobsData?.jobs || jobsData.jobs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              No jobs matching filters were found.
            </CardContent>
          </Card>
        ) : (
          <div className="border border-border rounded-lg bg-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>Job ID / Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Worker Node</TableHead>
                  <TableHead>Retries</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Queued At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobsData.jobs.map((job: AdminJob) => (
                  <>
                    <TableRow key={job.id} className="hover:bg-muted/50 transition-colors">
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => toggleExpand(job.id)}
                        >
                          {expandedJobId === job.id ? (
                            <ChevronUp size={16} />
                          ) : (
                            <ChevronDown size={16} />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell className="font-medium">
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm">{job.task_name}</span>
                          <span
                            className="text-xs text-muted-foreground font-mono truncate max-w-[200px]"
                            title={job.id}
                          >
                            {job.id}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(job.status)}</TableCell>
                      <TableCell
                        className="text-sm font-mono truncate max-w-[150px]"
                        title={job.worker || "None"}
                      >
                        {job.worker || "-"}
                      </TableCell>
                      <TableCell className="text-sm">{job.retries}</TableCell>
                      <TableCell className="text-sm">{formatTime(job.processing_time)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={retryMutation.isPending}
                          onClick={() => retryMutation.mutate(job.id)}
                          className="h-8 hover:bg-primary hover:text-white transition-colors"
                        >
                          <RefreshCw
                            className={`h-3.5 w-3.5 mr-1 ${retryMutation.isPending && retryMutation.variables === job.id ? "animate-spin" : ""}`}
                          />
                          Retry
                        </Button>
                      </TableCell>
                    </TableRow>
                    {expandedJobId === job.id && (
                      <TableRow className="bg-muted/20">
                        <TableCell colSpan={8} className="p-4 border-t border-border">
                          <div className="space-y-4 text-sm max-w-4xl">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold mb-1 text-xs uppercase tracking-wider text-muted-foreground">
                                  Payload Arguments
                                </h4>
                                <pre className="bg-surface border border-border rounded p-3 text-xs overflow-x-auto font-mono text-foreground max-h-48">
                                  {JSON.stringify(job.payload ?? null, null, 2)}
                                </pre>
                              </div>
                              <div>
                                <h4 className="font-semibold mb-1 text-xs uppercase tracking-wider text-muted-foreground">
                                  Execution Result
                                </h4>
                                <pre className="bg-surface border border-border rounded p-3 text-xs overflow-x-auto font-mono text-foreground max-h-48">
                                  {job.result !== undefined && job.result !== null
                                    ? JSON.stringify(job.result, null, 2)
                                    : "None"}
                                </pre>
                              </div>
                            </div>
                            {job.error !== undefined && job.error !== null && (
                              <div>
                                <h4 className="font-semibold mb-1 text-xs uppercase tracking-wider text-muted-foreground text-destructive">
                                  Error Traceback
                                </h4>
                                <pre className="bg-destructive/5 border border-destructive/20 text-destructive rounded p-3 text-xs overflow-x-auto font-mono max-h-60">
                                  {typeof job.error === "string"
                                    ? job.error
                                    : JSON.stringify(job.error, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}
              </TableBody>
            </Table>
            <div className="flex justify-between items-center p-4 border-t border-border bg-muted/20">
              <span className="text-xs text-muted-foreground">
                Showing Page {page} of {totalPages} ({jobsData.total} total jobs)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
