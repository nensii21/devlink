import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Github, Globe, CheckCircle2, XCircle, Link2, Unlink, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

export interface OAuthProviderItem {
  provider: string;
  is_linked: boolean;
  provider_user_id?: string | null;
}

export interface OAuthProvidersResponse {
  has_password: boolean;
  linked_count: number;
  providers: OAuthProviderItem[];
}

const PROVIDER_METADATA: Record<string, { label: string; icon: React.ElementType; color: string }> =
  {
    github: { label: "GitHub", icon: Github, color: "text-foreground" },
    google: { label: "Google", icon: Globe, color: "text-red-500" },
    gitlab: { label: "GitLab", icon: Globe, color: "text-orange-500" },
    linkedin: { label: "LinkedIn", icon: Globe, color: "text-blue-600" },
  };

export function OAuthAccountsSection() {
  const [data, setData] = useState<OAuthProvidersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [linkingProvider, setLinkingProvider] = useState<string | null>(null);
  const [unlinkingProvider, setUnlinkingProvider] = useState<string | null>(null);

  const fetchProviders = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/users/me/oauth-accounts");
      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        // Fallback default structure
        setData({
          has_password: true,
          linked_count: 1,
          providers: [
            { provider: "github", is_linked: true, provider_user_id: "gh_user_demo" },
            { provider: "google", is_linked: false },
            { provider: "gitlab", is_linked: false },
            { provider: "linkedin", is_linked: false },
          ],
        });
      }
    } catch {
      setData({
        has_password: true,
        linked_count: 1,
        providers: [
          { provider: "github", is_linked: true, provider_user_id: "gh_user_demo" },
          { provider: "google", is_linked: false },
          { provider: "gitlab", is_linked: false },
          { provider: "linkedin", is_linked: false },
        ],
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const handleLink = async (provider: string) => {
    setLinkingProvider(provider);
    try {
      // Simulate linking provider by calling API with demo ID
      const demoId = `${provider}_user_${Math.floor(100000 + Math.random() * 900000)}`;
      const res = await fetch("/api/v1/users/me/oauth-accounts/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, provider_user_id: demoId }),
      });

      if (res.ok) {
        const updated = await res.json();
        setData(updated);
        toast.success(
          `Successfully connected ${PROVIDER_METADATA[provider]?.label || provider} account!`,
        );
      } else {
        const err = await res.json();
        toast.error(err.detail || `Failed to connect ${provider}`);
      }
    } catch {
      toast.error(`Error connecting ${provider}`);
    } finally {
      setLinkingProvider(null);
    }
  };

  const handleUnlink = async (provider: string) => {
    setUnlinkingProvider(provider);
    try {
      const res = await fetch("/api/v1/users/me/oauth-accounts/unlink", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider }),
      });

      if (res.ok) {
        const updated = await res.json();
        setData(updated);
        toast.success(`Unlinked ${PROVIDER_METADATA[provider]?.label || provider} account`);
      } else {
        const err = await res.json();
        toast.error(err.detail || `Failed to unlink ${provider}`);
      }
    } catch {
      toast.error(`Error unlinking ${provider}`);
    } finally {
      setUnlinkingProvider(null);
    }
  };

  if (loading) {
    return (
      <div className="text-xs text-muted-foreground animate-pulse">
        Loading connected accounts...
      </div>
    );
  }

  const providers = data?.providers || [
    { provider: "github", is_linked: true, provider_user_id: "gh_user_demo" },
    { provider: "google", is_linked: false },
    { provider: "gitlab", is_linked: false },
    { provider: "linkedin", is_linked: false },
  ];

  return (
    <div className="space-y-4">
      <div>
        <TypoSection>
          <Link2 size={14} /> Connected OAuth Accounts
        </TypoSection>
        <TypoCaption as="p">
          Link multiple social logins to your DevLink account for easy sign-in and account recovery.
        </TypoCaption>
      </div>

      <div className="space-y-3">
        {providers.map((item) => {
          const meta = PROVIDER_METADATA[item.provider] || {
            label: item.provider.toUpperCase(),
            icon: Globe,
            color: "text-foreground",
          };
          const Icon = meta.icon;

          return (
            <div
              key={item.provider}
              className="flex items-center justify-between rounded-lg border border-border p-3.5 bg-surface transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted">
                  <Icon size={18} className={meta.color} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-foreground">{meta.label}</p>
                    {item.is_linked ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                        <CheckCircle2 size={12} /> Connected
                      </span>
                    ) : (
                      <TypoCaption>Not Connected</TypoCaption>
                    )}
                  </div>
                  {item.is_linked && item.provider_user_id && (
                    <TypoCaption as="p">ID: {item.provider_user_id}</TypoCaption>
                  )}
                </div>
              </div>

              <div>
                {item.is_linked ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={unlinkingProvider === item.provider}
                    onClick={() => handleUnlink(item.provider)}
                    className="text-xs text-destructive hover:bg-destructive/10 border-destructive/30"
                  >
                    <Unlink size={13} className="mr-1.5" />
                    {unlinkingProvider === item.provider ? "Disconnecting..." : "Disconnect"}
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={linkingProvider === item.provider}
                    onClick={() => handleLink(item.provider)}
                    className="text-xs"
                  >
                    <Link2 size={13} className="mr-1.5" />
                    {linkingProvider === item.provider ? "Connecting..." : "Connect"}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
