import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, Avatar } from "@/components/shared/primitives";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import {
  Trash2,
  Eye,
  EyeOff,
  Download,
  User,
  Shield,
  Bell,
  Sun,
  Moon,
  Monitor,
  Lock,
  Smartphone,
  Globe,
  KeyRound,
  Laptop,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi } from "@/api";
import { useTheme } from "@/context/ThemeContext";

const tabs = ["Account", "Privacy", "Notifications", "Appearance", "Security"] as const;
type Tab = (typeof tabs)[number];

const tabIcons: Record<Tab, React.ReactNode> = {
  Account: <User size={16} />,
  Privacy: <Globe size={16} />,
  Notifications: <Bell size={16} />,
  Appearance: <Sun size={16} />,
  Security: <Lock size={16} />,
};

export const Route = createFileRoute("/_app/settings")({
  head: () => ({
    meta: [
      { title: "Settings — DevLink" },
      {
        name: "description",
        content:
          "Manage your DevLink account, privacy, notifications, appearance, and security settings.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const [tab, setTab] = useState<Tab>("Account");
  const { theme, setTheme } = useTheme();

  // Account State
  const [name, setName] = useState(currentUser.name);
  const [handle, setHandle] = useState(currentUser.handle);
  const [email, setEmail] = useState("nancy@devlink.io");
  const [bio, setBio] = useState("Product engineer. React / Postgres / Rust.");
  const [website, setWebsite] = useState("https://devlink.io/nancy");
  const [savingAccount, setSavingAccount] = useState(false);

  // Privacy State
  const [profileVisibility, setProfileVisibility] = useState<"public" | "connections" | "private">(
    "public",
  );
  const [showOnlineStatus, setShowOnlineStatus] = useState(true);
  const [searchIndexing, setSearchIndexing] = useState(true);
  const [dmPermission, setDmPermission] = useState<"everyone" | "connections" | "nobody">(
    "everyone",
  );
  const [activityVisibility, setActivityVisibility] = useState(true);
  const [savingPrivacy, setSavingPrivacy] = useState(false);

  // Notifications State
  const [emailNotifications, setEmailNotifications] = useState({
    directMessages: true,
    builderRequests: true,
    projectMentions: true,
    hackathonDeadlines: true,
    productUpdates: false,
  });
  const [digestFrequency, setDigestFrequency] = useState<"realtime" | "daily" | "weekly">("daily");
  const [savingNotifications, setSavingNotifications] = useState(false);

  // Appearance State
  const [density, setDensity] = useState<"compact" | "comfortable" | "spacious">("comfortable");
  const [accentColor, setAccentColor] = useState<"indigo" | "emerald" | "violet" | "amber">(
    "indigo",
  );

  // Security State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Avatar & Banner state
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(currentUser.avatar);
  const [bannerUrl, setBannerUrl] = useState<string | null>(
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=400&fit=crop&auto=format",
  );

  const handleConfirmDelete = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    window.location.href = "/";
  };

  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";
  const lbl = "mb-1 block text-[13px] font-semibold text-foreground";

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">User Settings</h1>
        <p className="text-[13px] text-muted-foreground">
          Manage your account profile, privacy choices, notifications, visual theme, and security
          controls.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
        {/* Navigation Sidebar Tabs */}
        <Card className="p-2 h-fit">
          <nav className="space-y-1">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-[13px] font-medium transition-colors cursor-pointer text-left",
                  tab === t
                    ? "bg-primary-soft text-primary font-semibold shadow-2xs"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {tabIcons[t]}
                {t}
              </button>
            ))}
          </nav>
        </Card>

        {/* Content Area */}
        <Card className="p-6">
          <div className="border-b border-border pb-3 mb-5">
            <h2 className="text-[16px] font-bold text-foreground flex items-center gap-2">
              {tabIcons[tab]} {tab} Settings
            </h2>
          </div>

          <div className="space-y-6">
            {/* 1. ACCOUNT TAB */}
            {tab === "Account" && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (savingAccount) return;
                  setSavingAccount(true);
                  try {
                    await new Promise((r) => setTimeout(r, 600));
                    toast.success("Account profile updated successfully");
                  } finally {
                    setSavingAccount(false);
                  }
                }}
                className="space-y-5"
              >
                <div className="flex items-center gap-4 border-b border-border/60 pb-5">
                  <Avatar src={currentUser.avatar} alt={name} size={64} />
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{name}</h3>
                    <p className="text-xs text-muted-foreground">@{handle}</p>
                    <button
                      type="button"
                      onClick={() => toast.info("Avatar upload is ready")}
                      className="mt-2 text-[12px] text-primary hover:underline font-medium"
                    >
                      Change profile picture
                    </button>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Full Name</label>
                    <input
                      className={inp}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className={lbl}>Username</label>
                    <input
                      className={inp}
                      value={handle}
                      onChange={(e) => setHandle(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className={lbl}>Email Address</label>
                  <input
                    type="email"
                    className={inp}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className={lbl}>Bio</label>
                  <textarea
                    rows={3}
                    className={inp}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    placeholder="Tell the DevLink community about your skills and interests..."
                  />
                </div>

                <div>
                  <label className={lbl}>Personal Website / Portfolio</label>
                  <input
                    type="url"
                    className={inp}
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://yourportfolio.com"
                  />
                </div>

                <div className="pt-2">
                  <LoadingButton
                    type="submit"
                    loading={savingAccount}
                    loadingText="Saving account..."
                  >
                    Save account changes
                  </LoadingButton>
                </div>
              </form>
            )}

            {/* 2. PRIVACY TAB */}
            {tab === "Privacy" && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (savingPrivacy) return;
                  setSavingPrivacy(true);
                  try {
                    await new Promise((r) => setTimeout(r, 600));
                    toast.success("Privacy preferences saved");
                  } finally {
                    setSavingPrivacy(false);
                  }
                }}
                className="space-y-6"
              >
                <div>
                  <label className={lbl}>Profile Visibility</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Control who can view your full developer profile and project contributions.
                  </p>
                  <select
                    value={profileVisibility}
                    onChange={(e) =>
                      setProfileVisibility(e.target.value as "public" | "connections" | "private")
                    }
                    className={inp}
                  >
                    <option value="public">Public (Everyone on DevLink & search engines)</option>
                    <option value="connections">Connections Only (Only approved builders)</option>
                    <option value="private">Private (Only you)</option>
                  </select>
                </div>

                <div>
                  <label className={lbl}>Direct Message Permissions</label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Specify who is allowed to send you direct messages on DevLink.
                  </p>
                  <select
                    value={dmPermission}
                    onChange={(e) =>
                      setDmPermission(e.target.value as "everyone" | "connections" | "nobody")
                    }
                    className={inp}
                  >
                    <option value="everyone">Everyone</option>
                    <option value="connections">Connections Only</option>
                    <option value="nobody">Nobody</option>
                  </select>
                </div>

                <div className="space-y-4 border-t border-border pt-4">
                  <label className="flex items-center justify-between cursor-pointer">
                    <div>
                      <p className="text-[13px] font-semibold text-foreground">
                        Show Online Status
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Display an active badge when you are online in DevLink workspace.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={showOnlineStatus}
                      onChange={(e) => setShowOnlineStatus(e.target.checked)}
                      className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                    />
                  </label>

                  <label className="flex items-center justify-between cursor-pointer">
                    <div>
                      <p className="text-[13px] font-semibold text-foreground">
                        Search Engine Indexing
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Allow search engines (Google, Bing) to index your public portfolio.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={searchIndexing}
                      onChange={(e) => setSearchIndexing(e.target.checked)}
                      className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                    />
                  </label>

                  <label className="flex items-center justify-between cursor-pointer">
                    <div>
                      <p className="text-[13px] font-semibold text-foreground">
                        Activity Stream Privacy
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Broadcast project commits and team matches on community feed.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={activityVisibility}
                      onChange={(e) => setActivityVisibility(e.target.checked)}
                      className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                    />
                  </label>
                </div>

                <div className="pt-2">
                  <LoadingButton
                    type="submit"
                    loading={savingPrivacy}
                    loadingText="Updating privacy..."
                  >
                    Save privacy preferences
                  </LoadingButton>
                </div>
              </form>
            )}

            {/* 3. NOTIFICATIONS TAB */}
            {tab === "Notifications" && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (savingNotifications) return;
                  setSavingNotifications(true);
                  try {
                    await new Promise((r) => setTimeout(r, 600));
                    toast.success("Notification preferences updated");
                  } finally {
                    setSavingNotifications(false);
                  }
                }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-[14px] font-semibold text-foreground mb-3">
                    Email Notifications
                  </h3>
                  <div className="space-y-3">
                    {[
                      {
                        key: "directMessages",
                        label: "Direct Messages",
                        desc: "When someone sends you a message",
                      },
                      {
                        key: "builderRequests",
                        label: "Builder Requests",
                        desc: "When a developer invites you to connect",
                      },
                      {
                        key: "projectMentions",
                        label: "Project Mentions",
                        desc: "When you are tagged in project issues or code reviews",
                      },
                      {
                        key: "hackathonDeadlines",
                        label: "Hackathon Reminders",
                        desc: "Upcoming submission deadlines for registered hackathons",
                      },
                      {
                        key: "productUpdates",
                        label: "Product Announcements",
                        desc: "News about new DevLink platform features",
                      },
                    ].map((item) => (
                      <label
                        key={item.key}
                        className="flex items-center justify-between border-b border-border/50 pb-3 cursor-pointer"
                      >
                        <div>
                          <p className="text-[13px] font-medium text-foreground">{item.label}</p>
                          <p className="text-[11px] text-muted-foreground">{item.desc}</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={emailNotifications[item.key as keyof typeof emailNotifications]}
                          onChange={(e) =>
                            setEmailNotifications((prev) => ({
                              ...prev,
                              [item.key]: e.target.checked,
                            }))
                          }
                          className="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-[14px] font-semibold text-foreground mb-2">
                    Notification Digest
                  </h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    Choose how frequently summary emails are sent.
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "realtime", label: "Instant" },
                      { id: "daily", label: "Daily Digest" },
                      { id: "weekly", label: "Weekly Summary" },
                    ].map((opt) => (
                      <button
                        type="button"
                        key={opt.id}
                        onClick={() =>
                          setDigestFrequency(opt.id as "realtime" | "daily" | "weekly")
                        }
                        className={cn(
                          "rounded-md border p-2.5 text-[12px] font-medium transition-colors cursor-pointer text-center",
                          digestFrequency === opt.id
                            ? "border-primary bg-primary-soft text-primary font-semibold"
                            : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2">
                  <LoadingButton
                    type="submit"
                    loading={savingNotifications}
                    loadingText="Saving notifications..."
                  >
                    Save notification settings
                  </LoadingButton>
                </div>
              </form>
            )}

            {/* 4. APPEARANCE TAB */}
            {tab === "Appearance" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-[14px] font-semibold text-foreground mb-1">Color Theme</h3>
                  <p className="text-xs text-muted-foreground mb-4">
                    Select your preferred visual mode for DevLink UI.
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      {
                        id: "light",
                        label: "Light",
                        icon: <Sun size={20} className="text-amber-500" />,
                      },
                      {
                        id: "dark",
                        label: "Dark",
                        icon: <Moon size={20} className="text-purple-400" />,
                      },
                      {
                        id: "system",
                        label: "System",
                        icon: <Monitor size={20} className="text-blue-500" />,
                      },
                    ].map((mode) => (
                      <button
                        type="button"
                        key={mode.id}
                        onClick={() => setTheme(mode.id as "light" | "dark" | "system")}
                        className={cn(
                          "flex flex-col items-center justify-center gap-2 rounded-xl border p-4 transition-all cursor-pointer",
                          theme === mode.id
                            ? "border-primary bg-primary-soft/40 ring-2 ring-primary/20 text-primary font-semibold"
                            : "border-border bg-surface text-muted-foreground hover:border-border/80 hover:bg-muted/50",
                        )}
                      >
                        {mode.icon}
                        <span className="text-[13px]">{mode.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border-t border-border pt-4">
                  <h3 className="text-[14px] font-semibold text-foreground mb-1">
                    Interface Density
                  </h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    Adjust component spacing and font sizing.
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "compact", label: "Compact" },
                      { id: "comfortable", label: "Comfortable" },
                      { id: "spacious", label: "Spacious" },
                    ].map((d) => (
                      <button
                        type="button"
                        key={d.id}
                        onClick={() => {
                          setDensity(d.id as "compact" | "comfortable" | "spacious");
                          toast.success(`Density updated to ${d.label}`);
                        }}
                        className={cn(
                          "rounded-md border p-2.5 text-[12px] font-medium transition-colors cursor-pointer text-center",
                          density === d.id
                            ? "border-primary bg-primary-soft text-primary font-semibold"
                            : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
                        )}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border-t border-border pt-4">
                  <h3 className="text-[14px] font-semibold text-foreground mb-1">Accent Theme</h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    Customize brand highlight colors.
                  </p>
                  <div className="flex items-center gap-3">
                    {[
                      { id: "indigo", bg: "bg-indigo-600" },
                      { id: "emerald", bg: "bg-emerald-600" },
                      { id: "violet", bg: "bg-violet-600" },
                      { id: "amber", bg: "bg-amber-600" },
                    ].map((c) => (
                      <button
                        type="button"
                        key={c.id}
                        onClick={() => {
                          setAccentColor(c.id as "indigo" | "emerald" | "violet" | "amber");
                          toast.success(`Accent color set to ${c.id}`);
                        }}
                        className={cn(
                          "h-8 w-8 rounded-full transition-transform cursor-pointer flex items-center justify-center",
                          c.bg,
                          accentColor === c.id
                            ? "scale-110 ring-2 ring-offset-2 ring-primary"
                            : "opacity-80 hover:opacity-100",
                        )}
                        aria-label={`Select ${c.id} accent`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 5. SECURITY TAB */}
            {tab === "Security" && (
              <div className="space-y-8">
                {/* Change Password */}
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (newPassword !== confirmPassword) {
                      toast.error("New passwords do not match");
                      return;
                    }
                    if (savingPassword) return;
                    setSavingPassword(true);
                    try {
                      await new Promise((r) => setTimeout(r, 800));
                      toast.success("Password updated successfully");
                      setCurrentPassword("");
                      setNewPassword("");
                      setConfirmPassword("");
                    } finally {
                      setSavingPassword(false);
                    }
                  }}
                  className="space-y-4"
                >
                  <h3 className="text-[14px] font-semibold text-foreground flex items-center gap-2">
                    <KeyRound size={16} /> Update Password
                  </h3>
                  <div>
                    <label className={lbl}>Current Password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? "text" : "password"}
                        className={`${inp} pr-10`}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        aria-label={showCurrentPassword ? "Hide password" : "Show password"}
                      >
                        {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className={lbl}>New Password</label>
                      <div className="relative">
                        <input
                          type={showNewPassword ? "text" : "password"}
                          className={`${inp} pr-10`}
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          required
                          minLength={8}
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                          aria-label={showNewPassword ? "Hide password" : "Show password"}
                        >
                          {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className={lbl}>Confirm New Password</label>
                      <input
                        type="password"
                        className={inp}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        minLength={8}
                      />
                    </div>
                  </div>

                  <LoadingButton
                    type="submit"
                    loading={savingPassword}
                    loadingText="Updating password..."
                  >
                    Update Password
                  </LoadingButton>
                </form>

                {/* Two-Factor Auth */}
                <div className="border-t border-border pt-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-[14px] font-semibold text-foreground flex items-center gap-2">
                        <Shield size={16} /> Two-Factor Authentication (2FA)
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Add an extra layer of security to your DevLink account using authenticator
                        apps.
                      </p>
                    </div>
                    <Button
                      variant={twoFactorEnabled ? "destructive" : "outline"}
                      size="sm"
                      onClick={() => {
                        setTwoFactorEnabled(!twoFactorEnabled);
                        toast.success(
                          twoFactorEnabled
                            ? "2FA has been disabled"
                            : "2FA configuration initiated",
                        );
                      }}
                    >
                      {twoFactorEnabled ? "Disable 2FA" : "Enable 2FA"}
                    </Button>
                  </div>
                </div>

                {/* Active Sessions */}
                <div className="border-t border-border pt-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[14px] font-semibold text-foreground flex items-center gap-2">
                      <Laptop size={16} /> Active Sessions
                    </h3>
                    <button
                      type="button"
                      onClick={() => toast.success("Revoked all other sessions")}
                      className="text-xs text-destructive hover:underline font-medium"
                    >
                      Log out all other devices
                    </button>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between rounded-lg border border-border p-3 text-xs">
                      <div className="flex items-center gap-3">
                        <Laptop size={18} className="text-primary" />
                        <div>
                          <p className="font-semibold text-foreground">
                            Windows PC • Chrome (Current Session)
                          </p>
                          <p className="text-muted-foreground">San Francisco, CA • Active now</p>
                        </div>
                      </div>
                      <span className="rounded-full bg-success/10 px-2 py-0.5 font-semibold text-success text-[10px]">
                        Active
                      </span>
                    </div>

                    <div className="flex items-center justify-between rounded-lg border border-border p-3 text-xs opacity-75">
                      <div className="flex items-center gap-3">
                        <Smartphone size={18} className="text-muted-foreground" />
                        <div>
                          <p className="font-semibold text-foreground">
                            iPhone 15 • DevLink iOS App
                          </p>
                          <p className="text-muted-foreground">Seattle, WA • 2 hours ago</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => toast.success("Revoked session")}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        Revoke
                      </button>
                    </div>
                  </div>
                </div>

                {/* Data Export */}
                <div className="border-t border-border pt-5">
                  <div className="rounded-lg border border-border bg-muted/20 p-4 space-y-2">
                    <h3 className="text-[14px] font-semibold text-foreground flex items-center gap-2">
                      <Download size={16} /> Export Account Data
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Download a JSON archive of your personal profile, projects, messages,
                      bookmarks, and activity history.
                    </p>
                    <div className="pt-2">
                      <LoadingButton
                        loading={exporting}
                        loadingText="Preparing export..."
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
                      >
                        <Download size={15} className="mr-2" /> Export My Data
                      </LoadingButton>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* DANGER ZONE */}
      <Card className="p-5 border-destructive/30 bg-destructive/5 mt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-destructive flex items-center gap-1.5">
              <Trash2 size={16} /> Danger Zone
            </h3>
            <p className="text-xs text-muted-foreground">
              Permanently delete your DevLink account, projects, and all associated workspace data.
            </p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteModalOpen(true)}
            className="shrink-0"
          >
            Delete Account
          </Button>
        </div>
      </Card>

      <DeleteAccountModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        onConfirmDelete={handleConfirmDelete}
        userEmail={email}
      />
    </div>
  );
}
