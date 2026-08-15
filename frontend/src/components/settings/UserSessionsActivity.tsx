import { useState, useEffect } from "react";
import {
  Laptop,
  Smartphone,
  Globe,
  Shield,
  ShieldAlert,
  Eye,
  EyeOff,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { sessionsApi, type UserSession } from "@/api";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

function maskIpAddress(ip?: string | null): string {
  if (!ip) return "Unknown IP";
  if (ip === "127.0.0.1" || ip === "::1" || ip === "localhost") return ip;
  const parts = ip.split(".");
  if (parts.length === 4) {
    return `${parts[0]}.${parts[1]}.***.***`;
  }
  return ip.substring(0, Math.min(6, ip.length)) + "...";
}

function getDeviceIcon(deviceType?: string | null, os?: string | null) {
  const osLower = (os || "").toLowerCase();
  const typeLower = (deviceType || "").toLowerCase();

  if (typeLower.includes("mobile") || osLower.includes("ios") || osLower.includes("android")) {
    return <Smartphone className="h-5 w-5 text-primary" />;
  }
  if (
    typeLower.includes("desktop") ||
    typeLower.includes("laptop") ||
    osLower.includes("mac") ||
    osLower.includes("windows") ||
    osLower.includes("linux")
  ) {
    return <Laptop className="h-5 w-5 text-primary" />;
  }
  return <Globe className="h-5 w-5 text-muted-foreground" />;
}

function formatRelativeTime(dateStr?: string | null): string {
  if (!dateStr) return "Unknown";
  const date = new Date(dateStr);
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSec < 60) return "Active now";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} minutes ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hours ago`;
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)} days ago`;
  return date.toLocaleDateString();
}

export function UserSessionsActivity() {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [revokingOthers, setRevokingOthers] = useState(false);
  const [maskIp, setMaskIp] = useState(true);
  const [confirmRevokeOthersOpen, setConfirmRevokeOthersOpen] = useState(false);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await sessionsApi.getSessions();
      setSessions(data);
    } catch {
      toast.error("Failed to load active login sessions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleRevokeSession = async (sessionId: string) => {
    setRevokingId(sessionId);
    try {
      await sessionsApi.revokeSession(sessionId);
      toast.success("Session revoked successfully");
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch {
      toast.error("Failed to revoke session");
    } finally {
      setRevokingId(null);
    }
  };

  const handleRevokeOtherSessions = async () => {
    setRevokingOthers(true);
    try {
      const res = await sessionsApi.revokeOtherSessions();
      toast.success(res.message || `Revoked ${res.revoked_count} other session(s)`);
      fetchSessions();
      setConfirmRevokeOthersOpen(false);
    } catch {
      toast.error("Failed to revoke other sessions");
    } finally {
      setRevokingOthers(false);
    }
  };

  const otherSessionsCount = sessions.filter((s) => !s.is_current).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <TypoHeading as="h2">
            <Shield className="h-4 w-4 text-primary" /> Active Login Sessions
          </TypoHeading>
          <TypoCaption as="p">
            Review and manage devices currently signed into your account.
          </TypoCaption>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setMaskIp(!maskIp)}
            className="text-xs gap-1.5"
            title={maskIp ? "Show full IP addresses" : "Mask IP addresses"}
          >
            {maskIp ? <Eye size={14} /> : <EyeOff size={14} />}
            {maskIp ? "Show Full IP" : "Mask IP"}
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSessions}
            disabled={loading}
            className="text-xs gap-1.5"
            title="Refresh session list"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-sm text-muted-foreground border rounded-lg animate-pulse">
          Loading active sessions...
        </div>
      ) : sessions.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted-foreground border rounded-lg">
          No active login sessions found.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="rounded-lg border border-border divide-y divide-border overflow-hidden bg-card">
            {sessions.map((sess) => {
              const deviceLabel =
                sess.device_name ||
                `${sess.browser || "Browser"} on ${sess.operating_system || "Unknown OS"}`;
              const formattedIp = maskIp
                ? maskIpAddress(sess.ip_address)
                : sess.ip_address || "Unknown IP";

              return (
                <div
                  key={sess.id}
                  className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors ${
                    sess.is_current ? "bg-primary/5 dark:bg-primary/10" : "hover:bg-accent/40"
                  }`}
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted border border-border/50">
                      {getDeviceIcon(sess.device_type, sess.operating_system)}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-sm text-foreground">{deviceLabel}</span>
                        {sess.is_current && (
                          <Badge
                            variant="default"
                            className="bg-emerald-600 hover:bg-emerald-700 text-[11px] font-medium gap-1"
                          >
                            <CheckCircle2 size={11} /> Current Session
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                        <span className="font-mono bg-muted/60 px-1.5 py-0.5 rounded text-[11px]">
                          {formattedIp}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock size={12} />{" "}
                          {formatRelativeTime(sess.last_used_at || sess.created_at)}
                        </span>
                        {sess.user_agent && (
                          <span
                            className="hidden md:inline truncate max-w-[200px]"
                            title={sess.user_agent}
                          >
                            {sess.user_agent}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {!sess.is_current && (
                    <LoadingButton
                      variant="outline"
                      size="sm"
                      className="text-xs text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/30 shrink-0 self-end sm:self-center"
                      loading={revokingId === sess.id}
                      loadingText="Revoking..."
                      onClick={() => handleRevokeSession(sess.id)}
                    >
                      <Trash2 size={13} className="mr-1.5" /> Revoke
                    </LoadingButton>
                  )}
                </div>
              );
            })}
          </div>

          {otherSessionsCount > 0 && (
            <div className="flex items-center justify-between pt-2">
              <TypoCaption as="p">
                You have {otherSessionsCount} other active session
                {otherSessionsCount > 1 ? "s" : ""}.
              </TypoCaption>

              {!confirmRevokeOthersOpen ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs text-destructive border-destructive/30 hover:bg-destructive/10"
                  onClick={() => setConfirmRevokeOthersOpen(true)}
                >
                  <ShieldAlert size={14} className="mr-1.5" /> Revoke all other sessions
                </Button>
              ) : (
                <div className="flex items-center gap-2 bg-destructive/10 p-2 rounded-md border border-destructive/30">
                  <span className="text-xs font-medium text-destructive flex items-center gap-1">
                    <AlertTriangle size={13} /> Confirm revoke all other sessions?
                  </span>
                  <LoadingButton
                    variant="destructive"
                    size="sm"
                    className="text-xs h-7 px-2.5"
                    loading={revokingOthers}
                    loadingText="Revoking..."
                    onClick={handleRevokeOtherSessions}
                  >
                    Confirm Revoke
                  </LoadingButton>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs h-7 px-2"
                    onClick={() => setConfirmRevokeOthersOpen(false)}
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
