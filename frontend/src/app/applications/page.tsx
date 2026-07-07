"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getMyApplications,
  withdrawApplication,
  type ApplicationResponse,
  type UUID,
} from "@/lib/api";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { ApplicationStatusBadge } from "@/components/applications/ApplicationStatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export default function MyApplicationsPage() {
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<UUID | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["myApplications"],
    queryFn: () => getMyApplications(),
  });

  const apps = useMemo(() => {
    const list = data ?? [];
    const needle = q.trim().toLowerCase();
    if (!needle) return list;

    return list.filter((a) => {
      const hay = [
        a.message ?? "",
        a.portfolio_url ?? "",
        a.github_url ?? "",
        a.resume_url ?? "",
        a.status,
        a.id,
        a.project_id,
        a.flare_id,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(needle);
    });
  }, [data, q]);

  async function onWithdraw(id: UUID) {
    if (busyId) return;
    setBusyId(id);
    try {
      await withdrawApplication(id);
      toast.success("Application withdrawn");
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to withdraw application");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-bold tracking-tight text-foreground">My Applications</h1>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Track your status and withdraw pending applications.
          </p>
        </div>

        <div className="min-w-0 w-[280px] max-w-[280px]">
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search applications…"
            className={cn("bg-surface")}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-72" />
                <Skeleton className="h-3 w-64" />
                <Skeleton className="h-8 w-28" />
              </div>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="p-4">
          <p className="text-[13px] font-semibold text-destructive">Failed to load your applications</p>
          <p className="mt-1 text-[12px] text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </Card>
      ) : apps.length === 0 ? (
        <EmptyState
          title="No applications yet"
          desc="When you apply to a Builder Flare, your applications will appear here."
        />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {apps.map((a) => (
            <ApplicationCard
              key={a.id}
              app={a}
              busy={busyId === a.id}
              onWithdraw={() => onWithdraw(a.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ApplicationCard({
  app,
  busy,
  onWithdraw,
}: {
  app: ApplicationResponse;
  busy: boolean;
  onWithdraw: () => void;
}) {
  const canWithdraw = app.status === "pending" || app.status === "reviewing";

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <ApplicationStatusBadge status={app.status} />
            <span className="text-[12px] text-muted-foreground truncate">{app.id}</span>
          </div>

          {app.message && (
            <p className="mt-2 line-clamp-4 text-[13px] text-foreground">{app.message}</p>
          )}

          <div className="mt-2 flex flex-wrap gap-2">
            {app.portfolio_url && (
              <a
                href={app.portfolio_url}
                target="_blank"
                rel="noreferrer"
                className="text-[12px] font-medium text-primary hover:underline"
              >
                Portfolio
              </a>
            )}
            {app.github_url && (
              <a
                href={app.github_url}
                target="_blank"
                rel="noreferrer"
                className="text-[12px] font-medium text-primary hover:underline"
              >
                GitHub
              </a>
            )}
            {app.resume_url && (
              <a
                href={app.resume_url}
                target="_blank"
                rel="noreferrer"
                className="text-[12px] font-medium text-primary hover:underline"
              >
                Resume
              </a>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={!canWithdraw || busy}
            onClick={onWithdraw}
          >
            {busy ? "Withdrawing…" : "Withdraw"}
          </Button>
        </div>
      </div>
    </Card>
  );
}

