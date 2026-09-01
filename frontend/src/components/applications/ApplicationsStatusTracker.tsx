"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { applicationsApi } from "@/api/modules/applications";
import { type ApplicationResponse } from "@/lib/api";
import { ApplicationStatusBadge } from "./ApplicationStatusBadge";
import { Card, EmptyState, Skeleton } from "@/components/shared/primitives";
import { Button } from "@/components/ui/button";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { toast } from "sonner";
import {
  Briefcase,
  ExternalLink,
  FileText,
  Github,
  Globe,
  Loader2,
  Trash2,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function ApplicationsStatusTracker() {
  const queryClient = useQueryClient();
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null);

  const { data: applications = [], isLoading, error } = useQuery({
    queryKey: ["my-applications-status"],
    queryFn: () => applicationsApi.getMyApplications(),
  });

  const handleWithdraw = async (id: string) => {
    setWithdrawingId(id);
    try {
      await applicationsApi.withdraw(id);
      toast.success("Application withdrawn successfully");
      await queryClient.invalidateQueries({ queryKey: ["my-applications-status"] });
    } catch (err: any) {
      toast.error(err?.message || "Failed to withdraw application");
    } finally {
      setWithdrawingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-5 w-20" />
            </div>
            <Skeleton className="h-4 w-3/4" />
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-4 border-destructive/30 bg-destructive/5">
        <p className="text-xs font-semibold text-destructive">Failed to load submitted applications</p>
      </Card>
    );
  }

  if (applications.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="No project applications yet"
        desc="Apply to open projects using 1-Click DevLink Apply to track status here."
      />
    );
  }

  return (
    <div className="space-y-3">
      {applications.map((app: ApplicationResponse) => (
        <Card key={app.id} className="p-4 border-border bg-card transition-all hover:border-primary/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/50">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <TypoHeading as="h4" className="text-sm font-bold text-foreground">
                  Project Application
                </TypoHeading>
                <ApplicationStatusBadge status={app.status} />
              </div>
              <TypoCaption className="text-[11px] text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" /> Submitted {formatDistanceToNow(new Date(app.created_at))} ago
              </TypoCaption>
            </div>

            {/* Withdraw Action */}
            {(app.status === "pending" || app.status === "reviewing") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleWithdraw(app.id)}
                disabled={withdrawingId === app.id}
                className="text-xs text-destructive hover:bg-destructive/10 border-destructive/30 shrink-0 gap-1"
              >
                {withdrawingId === app.id ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Trash2 className="h-3 w-3" />
                )}
                Withdraw
              </Button>
            )}
          </div>

          {/* Application Details */}
          {app.message && (
            <p className="mt-3 text-xs text-foreground/90 bg-surface p-2.5 rounded-lg border border-border/50 leading-relaxed">
              "{app.message}"
            </p>
          )}

          {/* Links Grid */}
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {app.github_url && (
              <a
                href={app.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="h-3 w-3" /> GitHub
              </a>
            )}
            {app.portfolio_url && (
              <a
                href={app.portfolio_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Globe className="h-3 w-3" /> Portfolio
              </a>
            )}
            {app.resume_url && (
              <a
                href={app.resume_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
              >
                <FileText className="h-3 w-3" /> Resume
              </a>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
