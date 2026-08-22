import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import { auditService } from "@/services";
import type { AuditLog } from "@/api";
import { Activity } from "lucide-react";

interface AuditTimelineProps {
  entityType: string;
  entityId: string;
}

export function AuditTimeline({ entityType, entityId }: AuditTimelineProps) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await auditService.list({ entity_type: entityType });
        const filtered = data.filter((d) => d.entity_id === entityId);
        setLogs(filtered);
      } catch (e) {
        console.error("Failed to load audit logs", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [entityType, entityId]);

  if (loading) return <div className="text-sm text-muted-foreground">Loading timeline...</div>;
  if (logs.length === 0)
    return <div className="text-sm text-muted-foreground">No audit history found.</div>;

  return (
    <div className="flex flex-col space-y-4">
      {logs.map((log) => (
        <div key={log.id} className="flex gap-4 items-start">
          <div className="bg-primary/10 p-2 rounded-full mt-1">
            <Activity className="w-4 h-4 text-primary" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">
                {log.action.replace(/_/g, " ").toUpperCase()}
              </span>
              <span className="text-xs text-muted-foreground">
                {format(new Date(log.created_at), "MMM d, yyyy HH:mm")}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">By User {log.actor_id || "System"}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
