import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { SecurityDashboard } from "@/features/settings/components/security/SecurityDashboard";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  User,
  Shield,
  Bell,
  Palette,
  Lock,
  Download,
  Trash2,
  Camera,
  Upload,
  Save,
  Sun,
  Moon,
  Monitor,
  Eye,
  EyeOff,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi, authApi } from "@/api";
import { usersService } from "@/services";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

const tabs = [
  { id: "account", label: "Account", icon: User, description: "Personal profile and public information" },
  { id: "privacy", label: "Privacy", icon: Eye, description: "Visibility and data sharing settings" },
  { id: "notifications", label: "Notifications", icon: Bell, description: "Email and push notification preferences" },
  { id: "appearance", label: "Appearance", icon: Palette, description: "Theme and interface layout" },
  { id: "security", label: "Security", icon: Lock, description: "Password, two-factor authentication, and sessions" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export const Route = createFileRoute("/_app/settings")({
  head: () => ({
    meta: [
      { title: "User Settings — DevLink" },
      {
        name: "description",
        content: "Centralized settings page for account, privacy, notifications, appearance, and security.",
      },
    ],
  }),
  component: UserSettingsPage,
});

export function UserSettingsPage() {
  const [tab, setTab] = useState<TabId>("account");
  const [exporting, setExporting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [isBannerModalOpen, setIsBannerModalOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>(currentUser.avatar);
  const [bannerUrl, setBannerUrl] = useState<string | null>(
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=400&fit=crop&auto=format",
  );

  // Profile / Account state
  const [profileData, setProfileData] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    headline: "Full-Stack Developer",
    location: "San Francisco, CA",
    website: "https://devlink.io",
    bio: "",
    version: 1,
  });
  const [fullNameInput, setFullNameInput] = useState("");
  const [saveStatus, setSaveStatus] = useState<"saved" | "unsaved" | "saving" | "error">("saved");
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Privacy state
  const [privacySettings, setPrivacySettings] = useState({
    profilePublic: true,
    showEmail: false,
    showActivity: true,
    allowMessagesFromAnyone: true,
    showMatchScore: true,
  });

  // Notification state
  const [notificationSettings, setNotificationSettings] = useState({
    directMessages: true,
    collaborationInvites: true,
    mentionsAndComments: true,
    hackathonReminders: true,
    weeklyDigest: true,
    productUpdates: false,
  });

  // Appearance state
  const [themeMode, setThemeMode] = useState<"light" | "dark" | "system">("system");
  const [compactView, setCompactView] = useState(false);

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
            headline: (user as any).headline || "Full-Stack Developer",
            location: (user as any).location || "San Francisco, CA",
            website: (user as any).website || "https://devlink.io",
            bio: user.bio || "",
            version: user.version || 1,
          };
          setProfileData(loadedData);
          setFullNameInput(`${loadedData.first_name} ${loadedData.last_name}`.trim());
          setSaveStatus("saved");
        }
      } catch (err) {
        console.error("Failed to load user profile:", err);
      } finally {
        setLoadingProfile(false);
      }
    }
    loadProfile();
  }, []);

  const handleSaveAccount = async () => {
    setSaveStatus("saving");
    try {
      await usersService.updateMe({
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        username: profileData.username,
        email: profileData.email,
        bio: profileData.bio,
      });
      setSaveStatus("saved");
      toast.success("Account settings updated successfully");
    } catch {
      setSaveStatus("error");
      toast.error("Failed to update account settings");
    }
  };

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
    setSaveStatus("unsaved");
  };

  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-2 text-xs text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 placeholder:text-muted-foreground transition-all";
  const lbl = "mb-1 block text-xs font-medium text-foreground";

  return (
    <div className="mx-auto max-w-5xl space-y-4 py-2">
      {/* Header */}
      <div>
        <TypoHeading as="h1">User Settings</TypoHeading>
        <TypoCaption as="p">Manage your account, privacy, notifications, appearance, and security</TypoCaption>
      </div>

      <Separator />

      <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)] items-start">
        {/* Navigation Sidebar with 5 Tabs */}
        <aside>
          <nav className="sticky top-20 space-y-1 rounded-xl border border-border bg-card p-1.5">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition-all text-left",
                  tab === t.id
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <t.icon size={15} className="shrink-0" />
                <span className="truncate">{t.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Tab Content Panel */}
        <main className="min-h-[500px]">
          <Card className="p-5 space-y-5">
            {/* 1. ACCOUNT TAB */}
            {tab === "account" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Account Information</TypoHeading>
                  <TypoCaption as="p">Manage your public persona, avatar, and personal details</TypoCaption>
                </div>

                {/* Profile Media Cards */}
                <div className="grid gap-3 sm:grid-cols-2 rounded-lg border border-border bg-muted/20 p-3.5">
                  <div className="flex items-center gap-3">
                    <UserAvatar
                      src={avatarUrl}
                      name={currentUser.name}
                      size="lg"
                      editable
                      onImageUpload={(url) => setAvatarUrl(url)}
                    />
                    <div>
                      <p className="text-xs font-semibold text-foreground">Avatar Photo</p>
                      <TypoCaption as="p">PNG, JPG up to 5MB</TypoCaption>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsAvatarModalOpen(true)}
                        className="mt-1 h-7 text-[11px] px-2"
                      >
                        <Upload size={11} className="mr-1" /> Change Avatar
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
                    <div>
                      <p className="text-xs font-semibold text-foreground">Header Banner</p>
                      <TypoCaption as="p">Profile header image</TypoCaption>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsBannerModalOpen(true)}
                        className="mt-1 h-7 text-[11px] px-2"
                      >
                        <Camera size={11} className="mr-1" /> Edit Banner
                      </Button>
                    </div>
                  </div>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSaveAccount();
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
                        onChange={(e) => {
                          setProfileData((prev) => ({ ...prev, username: e.target.value }));
                          setSaveStatus("unsaved");
                        }}
                        placeholder="username"
                      />
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label className={lbl}>Email Address</label>
                      <input
                        className={inp}
                        type="email"
                        value={profileData.email}
                        onChange={(e) => {
                          setProfileData((prev) => ({ ...prev, email: e.target.value }));
                          setSaveStatus("unsaved");
                        }}
                        placeholder="email@example.com"
                      />
                    </div>
                    <div>
                      <label className={lbl}>Location</label>
                      <input
                        className={inp}
                        value={profileData.location}
                        onChange={(e) => {
                          setProfileData((prev) => ({ ...prev, location: e.target.value }));
                          setSaveStatus("unsaved");
                        }}
                        placeholder="City, Country"
                      />
                    </div>
                  </div>

                  <div>
                    <label className={lbl}>Professional Headline</label>
                    <input
                      className={inp}
                      value={profileData.headline}
                      onChange={(e) => {
                        setProfileData((prev) => ({ ...prev, headline: e.target.value }));
                        setSaveStatus("unsaved");
                      }}
                      placeholder="e.g. Senior Full Stack Engineer"
                    />
                  </div>

                  <div>
                    <label className={lbl}>Bio</label>
                    <textarea
                      rows={3}
                      className={inp}
                      value={profileData.bio}
                      onChange={(e) => {
                        setProfileData((prev) => ({ ...prev, bio: e.target.value }));
                        setSaveStatus("unsaved");
                      }}
                      placeholder="Brief overview about your experience..."
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                    <Button
                      type="submit"
                      size="sm"
                      className="gap-1.5 text-xs h-8"
                      disabled={saveStatus === "saving"}
                    >
                      <Save size={13} />
                      {saveStatus === "saving" ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                </form>
              </div>
            )}

            {/* 2. PRIVACY TAB */}
            {tab === "privacy" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Privacy & Visibility</TypoHeading>
                  <TypoCaption as="p">Control who can discover your profile, email, and activity</TypoCaption>
                </div>

                <div className="divide-y divide-border/60 rounded-lg border border-border bg-card">
                  {[
                    {
                      key: "profilePublic",
                      label: "Public Profile Visibility",
                      desc: "Allow your profile to appear in search engines and global builder directories",
                    },
                    {
                      key: "showEmail",
                      label: "Show Email Address",
                      desc: "Make your primary email address visible on your public developer profile",
                    },
                    {
                      key: "showActivity",
                      label: "Broadcast Activity Timeline",
                      desc: "Display recent commits, flares, and hackathon milestones publicly",
                    },
                    {
                      key: "allowMessagesFromAnyone",
                      label: "Direct Messaging Access",
                      desc: "Allow any registered builder to send you direct collaboration requests",
                    },
                    {
                      key: "showMatchScore",
                      label: "AI Match Score Display",
                      desc: "Show automated skill compatibility scores to potential project leads",
                    },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between p-3.5">
                      <div>
                        <Label htmlFor={item.key} className="text-xs font-medium text-foreground cursor-pointer">
                          {item.label}
                        </Label>
                        <TypoCaption as="p">{item.desc}</TypoCaption>
                      </div>
                      <Switch
                        id={item.key}
                        checked={privacySettings[item.key as keyof typeof privacySettings]}
                        onCheckedChange={(checked) => {
                          setPrivacySettings((prev) => ({ ...prev, [item.key]: checked }));
                          toast.success("Privacy settings updated");
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. NOTIFICATIONS TAB */}
            {tab === "notifications" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Notification Preferences</TypoHeading>
                  <TypoCaption as="p">Manage direct messaging alerts, invites, and digests</TypoCaption>
                </div>

                <div className="divide-y divide-border/60 rounded-lg border border-border bg-card">
                  {[
                    {
                      key: "directMessages",
                      label: "Direct Messages",
                      desc: "Receive real-time alerts when another developer messages you",
                    },
                    {
                      key: "collaborationInvites",
                      label: "Collaboration & Team Invites",
                      desc: "Notify when you are invited to join an active project team",
                    },
                    {
                      key: "mentionsAndComments",
                      label: "Mentions and Replies",
                      desc: "Notify when tagged in project tasks, flares, or issue comments",
                    },
                    {
                      key: "hackathonReminders",
                      label: "Hackathon Deadlines",
                      desc: "Reminders for upcoming team registrations and project submissions",
                    },
                    {
                      key: "weeklyDigest",
                      label: "Weekly Community Digest",
                      desc: "A weekly summary of trending projects, matching builders, and discussions",
                    },
                    {
                      key: "productUpdates",
                      label: "DevLink Product Updates",
                      desc: "Receive emails about major feature additions and developer news",
                    },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between p-3.5">
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
                          toast.success("Notification preferences saved");
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. APPEARANCE TAB */}
            {tab === "appearance" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Appearance & Theme</TypoHeading>
                  <TypoCaption as="p">Customize themes and interface layout density</TypoCaption>
                </div>

                <div className="space-y-3">
                  <label className={lbl}>Color Theme</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: "light", label: "Light", icon: Sun },
                      { id: "dark", label: "Dark", icon: Moon },
                      { id: "system", label: "System", icon: Monitor },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => {
                          setThemeMode(t.id as any);
                          toast.success(`Theme set to ${t.label}`);
                        }}
                        className={cn(
                          "flex flex-col items-center justify-center gap-2 rounded-lg border p-3.5 text-xs font-medium transition-all",
                          themeMode === t.id
                            ? "border-primary bg-primary/10 text-primary font-semibold ring-1 ring-primary"
                            : "border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground",
                        )}
                      >
                        <t.icon size={18} />
                        {t.label}
                      </button>
                    ))}
                  </div>

                  <Separator className="my-3" />

                  <div className="flex items-center justify-between p-1">
                    <div>
                      <p className="text-xs font-medium text-foreground">Compact Mode</p>
                      <TypoCaption as="p">Reduce padding for high-density information display</TypoCaption>
                    </div>
                    <Switch
                      checked={compactView}
                      onCheckedChange={(c) => {
                        setCompactView(c);
                        toast.success(c ? "Compact mode enabled" : "Standard mode enabled");
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 5. SECURITY TAB */}
            {tab === "security" && (
              <div className="space-y-4">
                <div className="border-b border-border pb-3">
                  <TypoHeading as="h2">Security & Authentication</TypoHeading>
                  <TypoCaption as="p">Manage password, two-factor authentication, and active sessions</TypoCaption>
                </div>

                <SecurityDashboard userEmail={profileData.email || "user@devlink.io"} />

                <Separator />

                {/* Danger Zone */}
                <div className="flex items-center justify-between rounded-lg border border-destructive/20 bg-destructive/5 p-3.5">
                  <div>
                    <p className="text-xs font-semibold text-destructive flex items-center gap-1.5">
                      <Trash2 size={14} /> Delete DevLink Account
                    </p>
                    <TypoCaption as="p">Permanently delete your profile, workspaces, and personal data</TypoCaption>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setDeleteModalOpen(true)}
                    className="h-8 text-xs"
                  >
                    Delete Account
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </main>
      </div>

      <DeleteAccountModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        onConfirmDelete={async () => {
          await new Promise((resolve) => setTimeout(resolve, 1500));
          window.location.href = "/";
        }}
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
