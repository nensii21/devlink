"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import type { ApplicationResponse, UUID } from "@/lib/api";
import {
  acceptApplication,
  getProjectApplications,
  rejectApplication,
  withdrawApplication,
} from "@/lib/api";
import { ApplicationStatusBadge } from "./ApplicationStatusBadge";
import { Button } from "@/components/ui/button";
import { Card, Skeleton } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";

type Props = {
  projectId: UUID;
  className?: string;
};

/**
 * Project owner view:
 * - list applicants
 * - Accept/Reject (optimistic) for pending
 */
export function ApplicationsList({ projectId, className }: Props) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["projectApplications", projectId],
    queryFn: () => getProjectApplications(projectId),
  });

  const [optimistic, setOptimistic] = useState<Record<UUID, ApplicationResponse["status"]>>({});

  const apps = useMemo(() => {
    if (!data) return [];
    return data.map((a) => ({
      ...a,
      status: optimistic[a.id] ?? a.status,
    }));
  }, [data, optimistic]);

  async function setStatus(id: UUID, status: "accepted" | "rejected") {
    // Optimistic update
    setOptimistic((prev) => ({ ...prev, [id]: status }));

    try {
      const apiFn = status === "accepted" ? acceptApplication : rejectApplication;
      await apiFn(id);
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update application");
      await refetch();
    } finally {
      setOptimistic((prev) => {
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
    }
  }

  async function onWithdraw(id: UUID) {
    setOptimistic((prev) => ({ ...prev, [id]: "withdrawn" }));
    try {
      await withdrawApplication(id);
      await refetch();
      toast.success("Application withdrawn");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to withdraw");
      await refetch();
    } finally {
      setOptimistic((prev) => {
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
    }
  }

  const [busyId, setBusyId] = useState<UUID | null>(null);
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return apps;
    // Without applicant display schema in response, we can only filter by links/message if present
    return apps.filter((a) => {
      const hay = [
        a.message ?? "",
        a.portfolio_url ?? "",
        a.github_url ?? "",
        a.resume_url ?? "",
        a.status,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(needle);
    });
  }, [apps, q]);

  if (error) {
    return (
      <Card className={cn("p-4", className)}>
        <p className="text-[13px] font-semibold text-destructive">Failed to load applications</p>
        <p className="mt-1 text-[12px] text-muted-foreground">
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </Card>
    );
  }

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[13px] font-semibold text-foreground">Applications</p>
          <p className="mt-1 text-[12px] text-muted-foreground">
            Review applicants and update status.
          </p>
        </div>
        <div className="min-w-0">
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search applications…"
            className="w-[220px] bg-surface"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="mt-4 grid gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-72" />
                </div>
                <Skeleton className="h-7 w-24" />
              </div>
            </Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="mt-6 text-center">
          <p className="text-[13px] font-semibold text-foreground">No applications found</p>
          <p className="mt-1 text-[12px] text-muted-foreground">Try adjusting your search.</p>
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-border">
          {filtered.map((a) => {
            const disabled = busyId === a.id || a.status !== "pending";
            const canReview = a.status === "pending";
            return (
              <li key={a.id} className="px-1 py-3">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <ApplicationStatusBadge status={a.status} />
                      <span className="text-[12px] text-muted-foreground">
                        Application ID: {a.id}
                      </span>
                    </div>

                    {a.message && (
                      <p className="mt-2 line-clamp-3 text-[13px] text-foreground">{a.message}</p>
                    )}

                    <div className="mt-2 flex flex-wrap gap-2">
                      {a.portfolio_url && (
                        <a
                          href={a.portfolio_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[12px] font-medium text-primary hover:underline"
                        >
                          Portfolio
                        </a>
                      )}
                      {a.github_url && (
                        <a
                          href={a.github_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[12px] font-medium text-primary hover:underline"
                        >
                          GitHub
                        </a>
                      )}
                      {a.resume_url && (
                        <a
                          href={a.resume_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[12px] font-medium text-primary hover:underline"
                        >
                          Resume
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={!canReview || disabled}
                        onClick={async () => {
                          setBusyId(a.id);
                          try {
                            await setStatus(a.id, "accepted");
                            toast.success("Application accepted");
                          } finally {
                            setBusyId(null);
                          }
                        }}
                      >
                        Accept
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={!canReview || disabled}
                        onClick={async () => {
                          setBusyId(a.id);
                          try {
                            await setStatus(a.id, "rejected");
                            toast.success("Application rejected");
                          } finally {
                            setBusyId(null);
                          }
                        }}
                      >
                        Reject
                      </Button>
                    </div>
                    {(a.status === "pending" || a.status === "reviewing") && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={disabled}
                        onClick={async () => {
                          setBusyId(a.id);
                          try {
                            await onWithdraw(a.id);
                          } finally {
                            setBusyId(null);
                          }
                        }}
                      >
                        Withdraw
                      </Button>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
