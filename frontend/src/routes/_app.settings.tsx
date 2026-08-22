import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { OAuthAccountsSection } from "@/components/settings/OAuthAccountsSection";
import { MFASection } from "@/features/settings/components/MFASection";
import { UserSessionsActivity } from "@/components/settings/UserSessionsActivity";
import { AvailabilitySettings } from "@/components/availability/AvailabilitySettings";


import { SecurityDashboard } from "@/features/settings/components/security/SecurityDashboard";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  User,
  Palette,
  Bell,
  Shield,
  CreditCard,
  Download,
  Trash2,
  Eye,
  EyeOff,
  Camera,
  Upload,
  Save,
  ChevronRight,
  ExternalLink,
  Calendar,
  HelpCircle,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi, authApi } from "@/api";
import { usersService } from "@/services";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

const tabs = [
  { id: "account", label: "Account", icon: User },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "availability", label: "Availability", icon: Calendar },
  { id: "privacy", label: "Privacy", icon: Lock },
  { id: "security", label: "Security", icon: Shield },
  { id: "billing", label: "Billing", icon: CreditCard },
  { id: "export", label: "Export Data", icon: Download },
] as const;

type TabId = (typeof tabs)[number]["id"];

export const Route = createFileRoute("/_app/settings")({
  head: () => ({
    meta: [
      { title: "Settings — DevLink" },
      {
        name: "description",
        content: "Manage your DevLink account, appearance, notifications and billing.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const [tab, setTab] = useState<TabId>("account");
  const [savingAccount, setSavingAccount] = useState(false);
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

  // Profile Privacy States
  const [isPrivateProfile, setIsPrivateProfile] = useState(false);
  const [privacySettings, setPrivacySettings] = useState({
    email: "private",
    github: "public",
    resume: "public",
    social_links: "public",
    availability: "public",
    activity: "public",
  });
  const [loadingPrivacy, setLoadingPrivacy] = useState(false);
  const [savingPrivacy, setSavingPrivacy] = useState(false);

  useEffect(() => {
    async function loadPrivacy() {
      setLoadingPrivacy(true);
      try {
        const settings = await usersService.getPrivacySettings();
        if (settings) {
          setPrivacySettings((prev) => ({ ...prev, ...settings }));
        }
        const user = await authApi.me();
        if (user) {
          setIsPrivateProfile(!!(user as any).is_private);
        }
      } catch (err) {
        console.error("Failed to load privacy settings:", err);
      } finally {
        setLoadingPrivacy(false);
      }
    }
    loadPrivacy();
  }, []);

  const handleSavePrivacy = async () => {
    setSavingPrivacy(true);
    try {
      await usersService.updatePrivacySettings(privacySettings);
      await usersService.updateMe({ is_private: isPrivateProfile });
      toast.success("Privacy settings updated successfully");
    } catch (err) {
      toast.error("Failed to update privacy settings");
      console.error(err);
    } finally {
      setSavingPrivacy(false);
    }
  };

  const handleConfirmDelete = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    window.location.href = "/";
  };

  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-[9px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground transition-all";
  const lbl = "mb-1.5 block text-[13px] font-medium text-foreground";
  const sectionTitle =
    "text-[13px] font-semibold text-muted-foreground uppercase tracking-wider mb-4";

  return (
    <div className="mx-auto max-w-5xl space-y-6 py-6">
      <div className="px-0">
        <TypoHeading as="h1">Settings</TypoHeading>
        <TypoCaption as="p">Manage your account settings and preferences</TypoCaption>
      </div>

      <Separator />

      <div className="grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)]">
        <aside className="space-y-1">
          <nav className="sticky top-20 space-y-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-[13px] font-medium transition-all",
                  tab === t.id
                    ? "bg-primary-soft text-primary font-semibold"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <t.icon size={16} className="shrink-0" />
                {t.label}
              </button>
            ))}

            <div className="pt-6">
              <div className="rounded-xl border border-border/70 bg-primary/5 p-4 space-y-2.5">
                <p className="text-xs font-semibold text-foreground">Need help?</p>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Visit our help center for security guides and FAQs.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs font-medium border-border hover:bg-muted justify-between h-8 px-2.5"
                  onClick={() => toast.info("Help center guides opening...")}
                >
                  <span>Visit Help Center</span>
                  <ExternalLink size={12} className="text-muted-foreground" />
                </Button>
              </div>
            </div>
          </nav>
        </aside>

        <main className="min-h-[500px]">
          <Card className="divide-y divide-border">
            {tab === "account" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Profile</TypoHeading>
                  <TypoCaption as="p">Manage your public profile information</TypoCaption>
                </div>

                <div className="rounded-lg border border-border bg-muted/30 p-5 space-y-4">
                  <TypoSection>Profile Media</TypoSection>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="flex flex-col items-center gap-3 rounded-lg border border-border bg-card p-5 text-center">
                      <UserAvatar
                        src={avatarUrl}
                        name={currentUser.name}
                        size="xl"
                        editable
                        onImageUpload={(url) => setAvatarUrl(url)}
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">Avatar</p>
                        <TypoCaption as="p">Recommended: 400x400px</TypoCaption>
                        <p className="text-xs font-semibold text-foreground">Avatar Photo</p>
                        <TypoCaption as="p">Drag & drop or crop before upload</TypoCaption>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsAvatarModalOpen(true)}
                        className="h-8 gap-1.5 text-xs"
                      >
                        <Upload size={13} />
                        Change
                      </Button>
                    </div>
                    <div className="flex flex-col items-center gap-3 rounded-lg border border-border bg-card p-5 text-center">
                      <div className="relative h-16 w-full overflow-hidden rounded-md bg-muted">
                        {bannerUrl ? (
                          <img
                            src={bannerUrl}
                            alt="Banner preview"
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="h-full w-full bg-gradient-to-r from-primary/30 to-purple-500/30" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">Banner</p>
                        <TypoCaption as="p">Recommended: 1200x400px</TypoCaption>
                        <p className="text-xs font-semibold text-foreground">Header Banner</p>
                        <TypoCaption as="p">3:1 aspect ratio landscape</TypoCaption>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsBannerModalOpen(true)}
                        className="h-8 gap-1.5 text-xs"
                      >
                        <Camera size={13} />
                        Edit
                      </Button>
                    </div>
                  </div>
                </div>                {loadingProfile ? (
                  <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                    Loading profile details...
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Conflict Resolution Banner */}
                    {saveStatus === "conflict" && (
                      <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 space-y-3">
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-destructive animate-pulse">Version Conflict Detected</p>
                          <p className="text-[13px] text-muted-foreground">
                            This profile has been modified on another device or session. What would you like to do?
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="destructive"
                            size="sm"
                            className="text-xs h-8"
                            onClick={() => performSave(true)}
                          >
                            Keep My Changes (Force Overwrite)
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs h-8"
                            onClick={async () => {
                              const user = await usersService.getMe();
                              if (user) {
                                const loadedData = {
                                  first_name: user.first_name || "",
                                  last_name: user.last_name || "",
                                  username: user.username || user.handle || "",
                                  email: user.email || "",
                                  bio: user.bio || "",
                                  version: user.version || 1,
                                };
                                setProfileData(loadedData);
                                setOriginalProfileData(loadedData);
                                setFullNameInput(`${loadedData.first_name} ${loadedData.last_name}`.trim());
                                setSaveStatus("saved");
                                setErrorMessage("");
                                toast.success("Profile reloaded from server");
                              }
                            }}
                          >
                            Discard & Reload Latest
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Auto-Save Settings Row */}
                    <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-muted/20 p-4">
                      <div className="flex items-center gap-3">
                        <Switch
                          id="auto-save"
                          checked={isAutoSaveEnabled}
                          onCheckedChange={setIsAutoSaveEnabled}
                        />
                        <div>
                          <Label htmlFor="auto-save" className="text-sm font-semibold text-foreground">
                            Enable Auto-Save
                          </Label>
                          <TypoCaption as="p">Changes save automatically after typing stops</TypoCaption>
                        </div>
                      </div>
                      {renderSaveStatusIndicator()}
                    </div>

                    <form
                      onSubmit={async (e) => {
                        e.preventDefault();
                        if (saveStatus === "saving") return;
                        await performSave(false);
                      }}
                      className="space-y-5"
                    >
                      <div className="grid gap-5 sm:grid-cols-2">
                        <div>
                          <label className={lbl}>Full name</label>
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
                      <div>
                        <label className={lbl}>Email</label>
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
                        <label className={lbl}>Bio</label>
                        <textarea
                          rows={3}
                          className={inp}
                          value={profileData.bio}
                          onChange={(e) =>
                            setProfileData((prev) => ({ ...prev, bio: e.target.value }))
                          }
                          placeholder="Tell us about yourself"
                        />
                        <TypoCaption as="p">Brief description for your profile</TypoCaption>
                      </div>

                      {errorMessage && (
                        <p className="text-xs font-medium text-destructive">{errorMessage}</p>
                      )}

                      <div className="flex items-center gap-3 pt-2">
                        <Button type="submit" className="gap-2" disabled={saveStatus === "saving" || saveStatus === "saved" || saveStatus === "conflict"}>
                          <Save size={15} />
                          {saveStatus === "saving" ? "Saving..." : "Save changes"}
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={handleDiscardChanges}
                          disabled={saveStatus === "saving" || saveStatus === "saved"}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  </div>
                )}

                <Separator />

                <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-5 space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <TypoSection>
                        <Trash2 size={15} /> Delete account
                      </TypoSection>
                      <TypoCaption as="p">
                        Permanently delete your account and all associated data. This action cannot
                        be undone.
                      </TypoCaption>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setDeleteModalOpen(true)}
                      className="shrink-0"
                    >
                      Delete
                    </Button>
                  </div>
                </div>

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
            )}

            {tab === "appearance" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Appearance</TypoHeading>
                  <TypoCaption as="p">Customize how DevLink looks for you</TypoCaption>
                </div>

                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Theme</p>
                      <TypoCaption as="p">Select your preferred color scheme</TypoCaption>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="default" size="sm" className="gap-2">
                        <Palette size={14} /> Light
                      </Button>
                      <Button variant="outline" size="sm" className="gap-2">
                        <Palette size={14} /> Dark
                      </Button>
                      <Button variant="outline" size="sm" className="gap-2">
                        <Palette size={14} /> System
                      </Button>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Reduced motion</p>
                      <TypoCaption as="p">Minimize animations across the interface</TypoCaption>
                    </div>
                    <Switch />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Compact mode</p>
                      <TypoCaption as="p">Reduce spacing for a denser layout</TypoCaption>
                    </div>
                    <Switch />
                  </div>
                </div>
              </div>
            )}

            {tab === "notifications" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Notifications</TypoHeading>
                  <TypoCaption as="p">Choose what notifications you receive</TypoCaption>
                </div>

                <div className="space-y-5">
                  <div>
                    <TypoSection>Push notifications</TypoSection>
                    <div className="space-y-4">
                      {[
                        {
                          key: "directMessages",
                          label: "Direct messages",
                          desc: "Someone sends you a direct message",
                        },
                        {
                          key: "builderRequests",
                          label: "Builder requests",
                          desc: "Someone invites you to collaborate",
                        },
                        {
                          key: "projectMentions",
                          label: "Project mentions",
                          desc: "You're mentioned in a project",
                        },
                        {
                          key: "hackathonDeadlines",
                          label: "Hackathon deadlines",
                          desc: "Upcoming hackathon deadlines",
                        },
                      ].map((item) => (
                        <div key={item.key} className="flex items-center justify-between">
                          <div>
                            <Label
                              htmlFor={item.key}
                              className="text-sm font-medium text-foreground"
                            >
                              {item.label}
                            </Label>
                            <TypoCaption as="p">{item.desc}</TypoCaption>
                          </div>
                          <Switch
                            id={item.key}
                            checked={
                              notificationSettings[item.key as keyof typeof notificationSettings]
                            }
                            onCheckedChange={(checked) =>
                              setNotificationSettings((prev) => ({ ...prev, [item.key]: checked }))
                            }
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <TypoSection>Email notifications</TypoSection>
                    <div className="space-y-4">
                      {[
                        {
                          key: "weeklyDigest",
                          label: "Weekly digest",
                          desc: "Weekly summary of your activity",
                        },
                        {
                          key: "marketingEmails",
                          label: "Marketing emails",
                          desc: "Product updates and tips",
                        },
                      ].map((item) => (
                        <div key={item.key} className="flex items-center justify-between">
                          <div>
                            <Label
                              htmlFor={item.key}
                              className="text-sm font-medium text-foreground"
                            >
                              {item.label}
                            </Label>
                            <TypoCaption as="p">{item.desc}</TypoCaption>
                          </div>
                          <Switch
                            id={item.key}
                            checked={
                              notificationSettings[item.key as keyof typeof notificationSettings]
                            }
                            onCheckedChange={(checked) =>
                              setNotificationSettings((prev) => ({ ...prev, [item.key]: checked }))
                            }
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  <Button
                    className="gap-2"
                    onClick={() => toast.success("Notification preferences saved")}
                  >
                    <Save size={15} /> Save preferences
                  </Button>
                </div>
              </div>
            )}

            {tab === "availability" && (
              <div className="p-6 space-y-6">
                <AvailabilitySettings />
              </div>
            )}

            {tab === "security" && <SecurityDashboard userEmail="nancy@example.com" />}
            {tab === "privacy" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Privacy Settings</TypoHeading>
                  <TypoCaption as="p">Control who can view your profile and activities</TypoCaption>
                </div>

                {loadingPrivacy ? (
                  <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                    Loading privacy settings...
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Public/Private Profile Toggle */}
                    <div className="rounded-lg border border-border bg-muted/30 p-5 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5 pr-4">
                          <Label className="text-sm font-semibold text-foreground">
                            Private Profile
                          </Label>
                          <TypoCaption as="p">
                            When enabled, your profile details will only be visible to you and followers.
                          </TypoCaption>
                        </div>
                        <Switch
                          checked={isPrivateProfile}
                          onCheckedChange={setIsPrivateProfile}
                        />
                      </div>
                    </div>

                    {/* Visibility Dropdowns */}
                    <div className="space-y-4">
                      <TypoSection>Visibility Controls</TypoSection>

                      <div className="grid gap-5 sm:grid-cols-2">
                        {/* Email Visibility */}
                        <div className="flex flex-col space-y-1.5">
                          <label className={lbl}>Email Visibility</label>
                          <select
                            className={inp}
                            value={privacySettings.email}
                            onChange={(e) =>
                              setPrivacySettings((prev) => ({
                                ...prev,
                                email: e.target.value,
                              }))
                            }
                          >
                            <option value="public">Public</option>
                            <option value="authenticated">Authenticated Users</option>
                            <option value="followers">Followers Only</option>
                            <option value="private">Private (Only Me)</option>
                          </select>
                          <TypoCaption>Who can see your public contact email address.</TypoCaption>
                        </div>

                        {/* Activity Visibility */}
                        <div className="flex flex-col space-y-1.5">
                          <label className={lbl}>Activity & Contribution History</label>
                          <select
                            className={inp}
                            value={privacySettings.activity}
                            onChange={(e) =>
                              setPrivacySettings((prev) => ({
                                ...prev,
                                activity: e.target.value,
                              }))
                            }
                          >
                            <option value="public">Public</option>
                            <option value="authenticated">Authenticated Users</option>
                            <option value="followers">Followers Only</option>
                            <option value="private">Private (Only Me)</option>
                          </select>
                          <TypoCaption>Who can view your reputation log & contribution heatmap.</TypoCaption>
                        </div>

                        {/* GitHub Visibility */}
                        <div className="flex flex-col space-y-1.5">
                          <label className={lbl}>GitHub Connection</label>
                          <select
                            className={inp}
                            value={privacySettings.github}
                            onChange={(e) =>
                              setPrivacySettings((prev) => ({
                                ...prev,
                                github: e.target.value,
                              }))
                            }
                          >
                            <option value="public">Public</option>
                            <option value="authenticated">Authenticated Users</option>
                            <option value="followers">Followers Only</option>
                            <option value="private">Private (Only Me)</option>
                          </select>
                          <TypoCaption>Visibility of your linked GitHub profile info.</TypoCaption>
                        </div>

                        {/* Resume Visibility */}
                        <div className="flex flex-col space-y-1.5">
                          <label className={lbl}>Resume / CV</label>
                          <select
                            className={inp}
                            value={privacySettings.resume}
                            onChange={(e) =>
                              setPrivacySettings((prev) => ({
                                ...prev,
                                resume: e.target.value,
                              }))
                            }
                          >
                            <option value="public">Public</option>
                            <option value="authenticated">Authenticated Users</option>
                            <option value="followers">Followers Only</option>
                            <option value="private">Private (Only Me)</option>
                          </select>
                          <TypoCaption>Who is allowed to view or download your uploaded resume.</TypoCaption>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 pt-4">
                      <Button onClick={handleSavePrivacy} className="gap-2" disabled={savingPrivacy}>
                        <Save size={15} />
                        {savingPrivacy ? "Saving..." : "Save Privacy Settings"}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {tab === "billing" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Billing</TypoHeading>
                  <TypoCaption as="p">Manage your subscription and payment methods</TypoCaption>
                </div>

                <div className="rounded-lg border border-border p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Current plan</p>
                      <TypoCaption as="p">You are on the Pro plan</TypoCaption>
                    </div>
                    <span className="rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
                      Pro
                    </span>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between text-sm">
                    <TypoCaption>Next invoice</TypoCaption>
                    <span className="font-medium text-foreground">November 4, 2026</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <TypoCaption>Amount</TypoCaption>
                    <span className="font-medium text-foreground">$19.00/month</span>
                  </div>
                  <Separator />
                  <Button variant="outline" size="sm" className="gap-2">
                    <ExternalLink size={14} /> View invoices
                  </Button>
                </div>

                <div className="rounded-lg border border-border p-5 space-y-3">
                  <TypoSection>Payment method</TypoSection>
                  <TypoCaption as="p">No payment method on file</TypoCaption>
                  <Button variant="outline" size="sm">
                    Add payment method
                  </Button>
                </div>
              </div>
            )}

            {tab === "export" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Export Data</TypoHeading>
                  <TypoCaption as="p">Download a copy of your DevLink data</TypoCaption>
                </div>

                <div className="rounded-lg border border-border p-5 space-y-4">
                  <div>
                    <TypoSection>Export your data</TypoSection>
                    <TypoCaption as="p">
                      Your data will be exported as a JSON file including your profile, skills,
                      projects, connections, messages, bookmarks, and activity history.
                    </TypoCaption>
                  </div>
                  <LoadingButton
                    className="gap-2"
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
                        toast.error("Failed to export data. Please try again.");
                      } finally {
                        setExporting(false);
                      }
                    }}
                  >
                    <Download size={16} className="mr-2" />
                    Export data
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
        userEmail="nancy@example.com"
      />
    </div>
  );
}
