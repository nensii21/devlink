import { useState, useEffect, useRef } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { SecurityDashboard } from "@/features/settings/components/security/SecurityDashboard";
import { BillingDashboard } from "@/features/settings/components/BillingDashboard";
import { ConnectedAccountsCard } from "@/features/settings/components/security/ConnectedAccountsCard";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  User,
  Palette,
  Bell,
  Shield,
  CreditCard,
  Code2,
  Download,
  Trash2,
  Camera,
  Upload,
  Save,
  ExternalLink,
  Key,
  Plus,
  Copy,
  CheckCircle2,
  Sun,
  Moon,
  Monitor,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi, authApi } from "@/api";
import { usersService } from "@/services";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

const tabs = [
  { id: "profile", label: "Profile", icon: User, description: "Personal info and avatar" },
  { id: "appearance", label: "Appearance", icon: Palette, description: "Theme and interface styling" },
  { id: "notifications", label: "Notifications", icon: Bell, description: "Email and push notifications" },
  { id: "security", label: "Security", icon: Shield, description: "Password, 2FA, and sessions" },
  { id: "billing", label: "Billing", icon: CreditCard, description: "Plans, usage, and invoices" },
  { id: "developer", label: "Developer Accounts", icon: Code2, description: "OAuth & API access tokens" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export const Route = createFileRoute("/_app/settings")({
  head: () => ({
    meta: [
      { title: "Settings — DevLink" },
      {
        name: "description",
        content: "Manage your DevLink account, appearance, notifications, security, and billing.",
      },
    ],
  }),
  component: SettingsPage,
});

export function SettingsPage() {
  const [tab, setTab] = useState<TabId>("profile");
  const [exporting, setExporting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(currentUser.avatar);
  const [bannerUrl, setBannerUrl] = useState<string | null>(
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=400&fit=crop&auto=format",
  );
  const [notificationSettings, setNotificationSettings] = useState({
    directMessages: true,
    builderRequests: true,
    projectMentions: false,
    hackathonDeadlines: true,
    weeklyDigest: true,
    marketingEmails: false,
  });

  // Profile Form States
  const [profileData, setProfileData] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    headline: "Full-Stack Developer & Open Source Contributor",
    location: "San Francisco, CA",
    website: "https://devlink.io",
    bio: "",
    version: 1,
  });
  const [originalProfileData, setOriginalProfileData] = useState<any>(null);
  const [fullNameInput, setFullNameInput] = useState("");
  const [isAutoSaveEnabled, setIsAutoSaveEnabled] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving" | "error" | "conflict">("saved");
  const [errorMessage, setErrorMessage] = useState("");
  const [loadingProfile, setLoadingProfile] = useState(true);
  // Distinct from `errorMessage`, which belongs to the save path. A profile
  // that could not be read leaves the form blank, and a blank form that says
  // nothing reads as "you have no name set" rather than "we could not ask".
  const [loadError, setLoadError] = useState("");

  // Appearance States
  const [selectedTheme, setSelectedTheme] = useState<"light" | "dark" | "system">("system");
  const [compactMode, setCompactMode] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Developer API Tokens Mock State
  const [apiTokens, setApiTokens] = useState([
    {
      id: "tok_1",
      name: "CLI Token (MacBook)",
      prefix: "dlk_live_49f8...",
      created: "2 weeks ago",
      lastUsed: "Just now",
    },
    {
      id: "tok_2",
      name: "GitHub Actions CI",
      prefix: "dlk_live_a81b...",
      created: "1 month ago",
      lastUsed: "Yesterday",
    },
  ]);
  const [newTokenName, setNewTokenName] = useState("");
  const [isCreatingToken, setIsCreatingToken] = useState(false);

  // Debounce timeout ref
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load user profile on mount
  useEffect(() => {
    async function loadProfile() {
      setLoadingProfile(true);
      try {
        const user = await usersService.getMe();
        if (user) {
          const loadedData = {
            first_name: user.first_name || "",
            last_name: user.last_name || "",
            username: user.username || user.handle || "",
            email: user.email || "",
            headline: user.headline || "Full-Stack Developer & Open Source Contributor",
            location: user.location || "San Francisco, CA",
            website: user.website || "https://devlink.io",
            bio: user.bio || "",
            version: user.version || 1,
          };
          setProfileData(loadedData);
          setOriginalProfileData(loadedData);
          setFullNameInput(`${loadedData.first_name} ${loadedData.last_name}`.trim());
          setSaveStatus("saved");
        } else {
          setLoadError("Could not load your profile. Your details are not shown.");
        }
      } catch (err) {
        console.error("Failed to load user profile:", err);
        setLoadError("Could not load your profile. Your details are not shown.");
      } finally {
        setLoadingProfile(false);
      }
    }
    loadProfile();
  }, []);

  const performSave = async (force = false) => {
    setSaveStatus("saving");
    setErrorMessage("");
    try {
      const payload: Record<string, any> = {
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        username: profileData.username,
        email: profileData.email,
        bio: profileData.bio,
      };
      if (!force) {
        payload.version = profileData.version;
      }
      const updatedUser = await usersService.updateMe(payload);
      if (updatedUser) {
        const newData = {
          ...profileData,
          first_name: (updatedUser as any).first_name || "",
          last_name: (updatedUser as any).last_name || "",
          username: (updatedUser as any).username || (updatedUser as any).handle || "",
          email: (updatedUser as any).email || "",
          bio: (updatedUser as any).bio || "",
          version: (updatedUser as any).version || 1,
        };
        setProfileData(newData);
        setOriginalProfileData(newData);
        setFullNameInput(`${newData.first_name} ${newData.last_name}`.trim());
        setSaveStatus("saved");
        toast.success("Profile saved successfully");
      }
    } catch (err: any) {
      if (err?.status === 409 || err?.statusCode === 409) {
        setSaveStatus("conflict");
        setErrorMessage("Version conflict: Profile updated elsewhere.");
        toast.error("Conflict detected: Profile updated elsewhere.");
      } else {
        setSaveStatus("error");
        setErrorMessage(err?.message || "Failed to save profile changes.");
        toast.error("Error saving profile changes.");
      }
    }
  };

  // Debounced auto-save listener
  useEffect(() => {
    if (!originalProfileData) return;

    const hasChanges =
      profileData.first_name !== originalProfileData.first_name ||
      profileData.last_name !== originalProfileData.last_name ||
      profileData.username !== originalProfileData.username ||
      profileData.email !== originalProfileData.email ||
      profileData.bio !== originalProfileData.bio ||
      profileData.headline !== originalProfileData.headline ||
      profileData.location !== originalProfileData.location ||
      profileData.website !== originalProfileData.website;

    if (!hasChanges) {
      setSaveStatus("saved");
      return;
    }

    setSaveStatus("unsaved");

    if (isAutoSaveEnabled) {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      debounceTimeoutRef.current = setTimeout(() => {
        performSave(false);
      }, 1500);
    }

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [
    profileData.first_name,
    profileData.last_name,
    profileData.username,
    profileData.email,
    profileData.bio,
    profileData.headline,
    profileData.location,
    profileData.website,
    isAutoSaveEnabled,
  ]);

  const handleNameChange = (val: string) => {
    setFullNameInput(val);
    const parts = val.trim().split(/\s+/);
    const firstName = parts[0] || "";
    const lastName = parts.slice(1).join(" ") || "";
    setProfileData((prev) => ({
      ...prev,
      first_name: firstName,
      last_name: lastName,
    }));
  };

  const handleDiscardChanges = () => {
    if (originalProfileData) {
      setProfileData(originalProfileData);
      setFullNameInput(`${originalProfileData.first_name} ${originalProfileData.last_name}`.trim());
      setSaveStatus("saved");
      setErrorMessage("");
      toast.success("Changes discarded");
    }
  };

  const renderSaveStatusIndicator = () => {
    switch (saveStatus) {
      case "saved":
        return (
          <div className="flex items-center gap-1.5 text-emerald-500 text-xs font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            All changes saved
          </div>
        );
      case "saving":
        return (
          <div className="flex items-center gap-1.5 text-muted-foreground text-xs font-medium animate-pulse">
            <div className="h-3 w-3 animate-spin rounded-full border border-primary border-t-transparent" />
            Saving...
          </div>
        );
      case "unsaved":
        return (
          <div className="flex items-center gap-1.5 text-amber-500 text-xs font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            Unsaved changes
          </div>
        );
      case "error":
        return (
          <div className="flex items-center gap-1.5 text-destructive text-xs font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
            Error saving
          </div>
        );
      case "conflict":
        return (
          <div className="flex items-center gap-1.5 text-destructive text-xs font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
            Conflict detected
          </div>
        );
      default:
        return null;
    }
  };

  const handleConfirmDelete = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    window.location.href = "/";
  };

  const handleCreateToken = () => {
    if (!newTokenName.trim()) return;
    const newToken = {
      id: `tok_${Date.now()}`,
      name: newTokenName.trim(),
      prefix: `dlk_live_${Math.random().toString(36).substring(2, 6)}...`,
      created: "Just now",
      lastUsed: "Never",
    };
    setApiTokens((prev) => [newToken, ...prev]);
    setNewTokenName("");
    setIsCreatingToken(false);
    toast.success("Personal API token created successfully");
  };

  const handleDeleteToken = (id: string) => {
    setApiTokens((prev) => prev.filter((t) => t.id !== id));
    toast.success("API token revoked");
  };

  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 placeholder:text-muted-foreground transition-all";
  const lbl = "mb-1 block text-xs font-medium text-foreground";

  return (
    <div className="mx-auto max-w-5xl space-y-4 py-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <TypoHeading as="h1">Settings</TypoHeading>
          <TypoCaption as="p">Manage your account preferences and developer configuration</TypoCaption>
        </div>
      </div>

      <Separator />

      <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)] items-start">
        {/* Navigation Sidebar */}
        <aside>
          <nav className="sticky top-20 space-y-1 rounded-xl border border-border bg-card p-1.5">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-all text-left",
                  tab === t.id
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <t.icon size={15} className="shrink-0" />
                <div className="min-w-0 flex-1 truncate">
                  <span>{t.label}</span>
                </div>
              </button>
            ))}

            <div className="pt-2">
              <div className="rounded-lg border border-border/70 bg-muted/30 p-2.5 space-y-1.5">
                <p className="text-[11px] font-semibold text-foreground">Need Assistance?</p>
                <p className="text-[10px] text-muted-foreground leading-tight">
                  Security policies and API documentation guides.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-[10px] font-medium h-7 px-2 justify-between"
                  onClick={() => toast.info("DevLink Help documentation opening...")}
                >
                  <span>Help Center</span>
                  <ExternalLink size={10} className="text-muted-foreground" />
                </Button>
              </div>
            </div>
          </nav>
        </aside>

        {/* Tab Content Panel */}
        <main className="min-h-[500px]">
          <Card className="p-4 sm:p-5 space-y-5">
            {/* 1. PROFILE TAB */}
            {tab === "profile" && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                  <div>
                    <TypoHeading as="h2">Profile</TypoHeading>
                    <TypoCaption as="p">Public identity and personal developer info</TypoCaption>
                  </div>
                  {renderSaveStatusIndicator()}
                </div>

                {/* Profile Media - Compact 2-column */}
                <div className="grid gap-3 sm:grid-cols-2 rounded-lg border border-border bg-muted/20 p-3.5">
                  <div className="flex items-center gap-3">
                    <UserAvatar
                      src={avatarUrl}
                      name={currentUser.name}
                      size="lg"
                      editable
                      onImageUpload={(url) => setAvatarUrl(url)}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-foreground">Avatar Photo</p>
                      <TypoCaption as="p">Square format, up to 5MB</TypoCaption>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsAvatarModalOpen(true)}
                        className="mt-1 h-7 gap-1 text-[11px] px-2"
                      >
                        <Upload size={11} /> Change
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="relative h-12 w-20 shrink-0 overflow-hidden rounded-md bg-muted border border-border">
                      {bannerUrl ? (
                        <img src={bannerUrl} alt="Banner" className="h-full w-full object-cover" />
                      ) : (
                        <div className="h-full w-full bg-gradient-to-r from-primary/30 to-purple-500/30" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-foreground">Header Banner</p>
                      <TypoCaption as="p">3:1 aspect ratio</TypoCaption>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsBannerModalOpen(true)}
                        className="mt-1 h-7 gap-1 text-[11px] px-2"
                      >
                        <Camera size={11} /> Edit
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Form Fields - 2 Column Grid */}
                {loadingProfile ? (
                  <div className="flex h-32 items-center justify-center text-xs text-muted-foreground">
                    Loading profile...
                  </div>
                ) : (
                  <form
                    onSubmit={async (e) => {
                      e.preventDefault();
                      if (saveStatus === "saving") return;
                      await performSave(false);
                    }}
                    className="space-y-3.5"
                  >
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className={lbl}>Full Name</label>
                        <input
                          className={inp}
                          value={fullNameInput}
                          onChange={(e) => handleNameChange(e.target.value)}
                          placeholder="Your full name"
                        />
                      </div>
                      <div>
                        <label className={lbl}>Username</label>
                        <input
                          className={inp}
                          value={profileData.username}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, username: e.target.value }))
                          }
                          placeholder="username"
                        />
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className={lbl}>Email Address</label>
                        <input
                          className={inp}
                          value={profileData.email}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, email: e.target.value }))
                          }
                          type="email"
                          placeholder="email@example.com"
                        />
                      </div>
                      <div>
                        <label className={lbl}>Location</label>
                        <input
                          className={inp}
                          value={profileData.location}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, location: e.target.value }))
                          }
                          placeholder="City, Country"
                        />
                      </div>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className={lbl}>Headline / Role</label>
                        <input
                          className={inp}
                          value={profileData.headline}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, headline: e.target.value }))
                          }
                          placeholder="e.g. Senior Frontend Engineer"
                        />
                      </div>
                      <div>
                        <label className={lbl}>Website / Portfolio</label>
                        <input
                          className={inp}
                          value={profileData.website}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, website: e.target.value }))
                          }
                          placeholder="https://..."
                        />
                      </div>
                    </div>

                    <div>
                      <label className={lbl}>Bio</label>
                      <textarea
                        rows={2}
                        className={inp}
                        value={profileData.bio}
                        onChange={(e) =>
                          setProfileData((prev) => ({ ...prev, bio: e.target.value }))
                        }
                        placeholder="Short summary about your developer background..."
                      />
                    </div>

                    {loadError && (
                      <p className="text-xs font-medium text-destructive">{loadError}</p>
                    )}

                    {errorMessage && (
                      <p className="text-xs font-medium text-destructive">{errorMessage}</p>
                    )}

                    {/* Compact Auto-Save + Action Buttons Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border">
                      <div className="flex items-center gap-2">
                        <Switch
                          id="auto-save"
                          checked={isAutoSaveEnabled}
                          onCheckedChange={setIsAutoSaveEnabled}
                        />
                        <Label htmlFor="auto-save" className="text-xs font-medium text-muted-foreground cursor-pointer">
                          Auto-save on typing
                        </Label>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleDiscardChanges}
                          disabled={saveStatus === "saving" || saveStatus === "saved"}
                          className="h-8 text-xs"
                        >
                          Discard
                        </Button>
                        <Button
                          type="submit"
                          size="sm"
                          className="gap-1.5 h-8 text-xs"
                          disabled={saveStatus === "saving" || saveStatus === "saved" || saveStatus === "conflict"}
                        >
                          <Save size={13} />
                          {saveStatus === "saving" ? "Saving..." : "Save Profile"}
                        </Button>
                      </div>
                    </div>
                  </form>
                )}

                <Separator className="my-2" />

                {/* Compact Danger Zone Card */}
                <div className="flex items-center justify-between rounded-lg border border-destructive/20 bg-destructive/5 p-3">
                  <div>
                    <p className="text-xs font-semibold text-destructive flex items-center gap-1.5">
                      <Trash2 size={13} /> Delete Account
                    </p>
                    <TypoCaption as="p">Permanently delete your profile and workspace data</TypoCaption>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setDeleteModalOpen(true)}
                    className="h-7 text-xs px-2.5"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            )}

            {/* 2. APPEARANCE TAB */}
            {tab === "appearance" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Appearance</TypoHeading>
                  <TypoCaption as="p">Customize themes and interface density</TypoCaption>
                </div>

                <div className="space-y-4">
                  {/* Theme Mode Selector */}
                  <div>
                    <label className={lbl}>Interface Theme</label>
                    <div className="grid grid-cols-3 gap-2.5">
                      {[
                        { id: "light", label: "Light", icon: Sun },
                        { id: "dark", label: "Dark", icon: Moon },
                        { id: "system", label: "System", icon: Monitor },
                      ].map((t) => (
                        <button
                          key={t.id}
                          type="button"
                          onClick={() => {
                            setSelectedTheme(t.id as any);
                            toast.success(`Theme set to ${t.label}`);
                          }}
                          className={cn(
                            "flex flex-col items-center justify-center gap-1.5 rounded-lg border p-3 text-xs font-medium transition-all",
                            selectedTheme === t.id
                              ? "border-primary bg-primary/10 text-primary font-semibold ring-1 ring-primary"
                              : "border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground",
                          )}
                        >
                          <t.icon size={16} />
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Compact Mode & Reduced Motion */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-foreground">Compact UI Layout</p>
                        <TypoCaption as="p">Increase screen density and reduce padding</TypoCaption>
                      </div>
                      <Switch
                        checked={compactMode}
                        onCheckedChange={(c) => {
                          setCompactMode(c);
                          toast.success(c ? "Compact density enabled" : "Default density restored");
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-foreground">Reduced Motion</p>
                        <TypoCaption as="p">Disable non-essential micro-animations</TypoCaption>
                      </div>
                      <Switch
                        checked={reducedMotion}
                        onCheckedChange={(c) => {
                          setReducedMotion(c);
                          toast.success(c ? "Reduced motion enabled" : "Motion enabled");
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 3. NOTIFICATIONS TAB */}
            {tab === "notifications" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Notifications</TypoHeading>
                  <TypoCaption as="p">Manage message alerts, builder invites, and digests</TypoCaption>
                </div>

                <div className="space-y-3">
                  <TypoSection>In-App & Email Alerts</TypoSection>
                  <div className="divide-y divide-border/60 rounded-lg border border-border bg-card">
                    {[
                      {
                        key: "directMessages",
                        label: "Direct Messages",
                        desc: "Notify when someone sends a private message",
                      },
                      {
                        key: "builderRequests",
                        label: "Collaboration & Team Invites",
                        desc: "Notify when invited to collaborate on a project",
                      },
                      {
                        key: "projectMentions",
                        label: "Project Mentions & Issues",
                        desc: "Notify when tagged in comments or issue assignments",
                      },
                      {
                        key: "hackathonDeadlines",
                        label: "Hackathon Deadlines",
                        desc: "Reminders for submissions and judging phases",
                      },
                      {
                        key: "weeklyDigest",
                        label: "Weekly Developer Digest",
                        desc: "Summary of trending projects, stars, and flares",
                      },
                      {
                        key: "marketingEmails",
                        label: "Product Announcements",
                        desc: "Major feature releases and DevLink platform updates",
                      },
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-3">
                        <div>
                          <Label htmlFor={item.key} className="text-xs font-medium text-foreground cursor-pointer">
                            {item.label}
                          </Label>
                          <TypoCaption as="p">{item.desc}</TypoCaption>
                        </div>
                        <Switch
                          id={item.key}
                          checked={notificationSettings[item.key as keyof typeof notificationSettings]}
                          onCheckedChange={(checked) => {
                            setNotificationSettings((prev) => ({ ...prev, [item.key]: checked }));
                            toast.success("Notification preferences updated");
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 4. SECURITY TAB */}
            {tab === "security" && (
              <div className="space-y-4">
                <SecurityDashboard userEmail={profileData.email || "user@devlink.io"} />
              </div>
            )}

            {/* 5. BILLING TAB */}
            {tab === "billing" && (
              <div className="space-y-4">
                <BillingDashboard />
              </div>
            )}

            {/* 6. DEVELOPER ACCOUNTS TAB */}
            {tab === "developer" && (
              <div className="space-y-5">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Developer Accounts & API Access</TypoHeading>
                  <TypoCaption as="p">Connect external git repositories and manage API tokens</TypoCaption>
                </div>

                {/* Connected OAuth Providers */}
                <ConnectedAccountsCard />

                <Separator />

                {/* Personal Access Tokens Section */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <TypoSection>Personal Access Tokens</TypoSection>
                      <TypoCaption as="p">API keys for CLI authentication and automated workflows</TypoCaption>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => setIsCreatingToken(true)}
                      className="gap-1 text-xs h-8"
                    >
                      <Plus size={12} /> Generate Token
                    </Button>
                  </div>

                  {isCreatingToken && (
                    <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2.5">
                      <p className="text-xs font-semibold text-foreground">Create New API Token</p>
                      <div className="flex gap-2">
                        <input
                          className={inp}
                          placeholder="Token description (e.g. CI runner)"
                          value={newTokenName}
                          onChange={(e) => setNewTokenName(e.target.value)}
                        />
                        <Button size="sm" onClick={handleCreateToken} className="h-8 text-xs px-3 shrink-0">
                          Create
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setIsCreatingToken(false)}
                          className="h-8 text-xs px-2 shrink-0"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    {apiTokens.map((tok) => (
                      <div
                        key={tok.id}
                        className="flex items-center justify-between rounded-lg border border-border bg-muted/20 p-2.5 text-xs"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <Key size={14} className="text-primary shrink-0" />
                          <div className="min-w-0">
                            <p className="font-semibold text-foreground truncate">{tok.name}</p>
                            <p className="font-mono text-[11px] text-muted-foreground">{tok.prefix}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(tok.prefix);
                              toast.success("Token copied to clipboard");
                            }}
                            className="h-7 px-2 text-[11px]"
                          >
                            <Copy size={11} /> Copy
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteToken(tok.id)}
                            className="h-7 px-2 text-[11px] text-destructive hover:bg-destructive/10 hover:border-destructive/30"
                          >
                            Revoke
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                {/* Export Data Box */}
                <div className="rounded-lg border border-border bg-card p-3.5 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-foreground">Export Account Data</p>
                    <TypoCaption as="p">Download a complete JSON snapshot of your data</TypoCaption>
                  </div>
                  <LoadingButton
                    size="sm"
                    loading={exporting}
                    loadingText="Exporting..."
                    onClick={async () => {
                      setExporting(true);
                      try {
                        const res = await exportApi.exportData();
                        const blob = new Blob([JSON.stringify(res.data, null, 2)], {
                          type: "application/json",
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `devlink-export-${new Date().toISOString().slice(0, 10)}.json`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        toast.success("Data exported successfully");
                      } catch {
                        toast.error("Failed to export data");
                      } finally {
                        setExporting(false);
                      }
                    }}
                    className="h-8 text-xs"
                  >
                    <Download size={13} className="mr-1.5" /> Export Data
                  </LoadingButton>
                </div>
              </div>
            )}
          </Card>
        </main>
      </div>

      <DeleteAccountModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        onConfirmDelete={handleConfirmDelete}
        userEmail={profileData.email || "user@devlink.io"}
      />

      <ImageCropUploadModal
        isOpen={isAvatarModalOpen}
        onClose={() => setIsAvatarModalOpen(false)}
        onUploadSuccess={(url) => setAvatarUrl(url)}
        mode="avatar"
        title="Upload Avatar Image"
      />
      <ImageCropUploadModal
        isOpen={isBannerModalOpen}
        onClose={() => setIsBannerModalOpen(false)}
        onUploadSuccess={(url) => setBannerUrl(url)}
        mode="banner"
        title="Upload Header Banner"
      />
    </div>
  );
}
