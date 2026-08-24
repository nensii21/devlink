import { useState, useEffect } from "react";
import { Activity, CheckCircle2, Wifi, Server, ShieldCheck } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export interface SystemStatus {
  status: "operational" | "degraded" | "outage";
  name: string;
  uptime: string;
  latency: number;
  lastChecked: Date;
  services: {
    name: string;
    status: "operational" | "degraded";
    latency: number;
  }[];
}

export function WorkspaceStatusIndicator() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    status: "operational",
    name: "DevLink Alpha",
    uptime: "99.98%",
    latency: 24,
    lastChecked: new Date(),
    services: [
      { name: "API Gateway", status: "operational", latency: 18 },
      { name: "Realtime WebSocket", status: "operational", latency: 26 },
      { name: "Database Cluster", status: "operational", latency: 12 },
      { name: "AI Inference Engine", status: "operational", latency: 42 },
    ],
  });

  const [isPinging, setIsPinging] = useState(false);

  // Live status updates every 15 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setIsPinging(true);
      setTimeout(() => {
        // Slight latency jitter simulating live telemetry
        const jitter = Math.floor(Math.random() * 8) - 4;
        const newLatency = Math.max(14, Math.min(48, 24 + jitter));
        setSystemStatus((prev) => ({
          ...prev,
          latency: newLatency,
          lastChecked: new Date(),
          services: prev.services.map((s) => ({
            ...s,
            latency: Math.max(10, s.latency + (Math.floor(Math.random() * 6) - 3)),
          })),
        }));
        setIsPinging(false);
      }, 500);
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Workspace Status: All systems operational"
          className={cn(
            "group inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-surface/90 px-2.5 py-1 text-xs font-medium text-muted-foreground transition-all",
            "hover:border-primary/40 hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary",
          )}
        >
          <span className="relative flex h-2 w-2">
            <span
              className={cn(
                "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                systemStatus.status === "operational" && "bg-emerald-400",
                systemStatus.status === "degraded" && "bg-amber-400",
                systemStatus.status === "outage" && "bg-red-400",
              )}
            />
            <span
              className={cn(
                "relative inline-flex h-2 w-2 rounded-full",
                systemStatus.status === "operational" && "bg-emerald-500",
                systemStatus.status === "degraded" && "bg-amber-500",
                systemStatus.status === "outage" && "bg-red-500",
              )}
            />
          </span>

          {/* Compact label */}
          <span className="hidden xl:inline text-[11px] font-medium text-foreground">
            {systemStatus.name}
          </span>
          <span className="hidden sm:inline text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
            Operational
          </span>
          <span className="text-[10px] text-muted-foreground hidden md:inline">
            ({systemStatus.latency}ms)
          </span>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-72 p-3 space-y-2.5">
        <DropdownMenuLabel className="p-0 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-emerald-500" />
            <div>
              <p className="text-xs font-semibold text-foreground">{systemStatus.name}</p>
              <p className="text-[10px] font-normal text-muted-foreground">Global Workspace Status</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Live
          </span>
        </DropdownMenuLabel>

        <DropdownMenuSeparator className="my-1" />

        {/* Global telemetry stats */}
        <div className="grid grid-cols-2 gap-2 rounded-lg border border-border/60 bg-muted/40 p-2.5 text-center">
          <div>
            <span className="text-[10px] text-muted-foreground block">Uptime</span>
            <span className="text-xs font-bold text-foreground">{systemStatus.uptime}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block">Avg Latency</span>
            <span className="text-xs font-bold text-foreground">{systemStatus.latency}ms</span>
          </div>
        </div>

        {/* Micro service breakdown */}
        <div className="space-y-1.5 pt-1">
          <p className="text-[11px] font-medium text-muted-foreground">Active Subsystems</p>
          {systemStatus.services.map((svc) => (
            <div
              key={svc.name}
              className="flex items-center justify-between text-xs py-0.5 px-1 rounded hover:bg-muted/50 transition-colors"
            >
              <span className="text-foreground text-[11px] flex items-center gap-1.5">
                <CheckCircle2 size={12} className="text-emerald-500 shrink-0" />
                {svc.name}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {svc.latency}ms
              </span>
            </div>
          ))}
        </div>

        <DropdownMenuSeparator className="my-1" />

        <div className="flex items-center justify-between text-[10px] text-muted-foreground px-1">
          <span>Updated {systemStatus.lastChecked.toLocaleTimeString()}</span>
          <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
            <Wifi size={10} /> Live Heartbeat
          </span>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
