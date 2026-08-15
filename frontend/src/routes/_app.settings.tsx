import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { UserAvatar } from "@/components/user-avatar";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { OAuthAccountsSection } from "@/components/settings/OAuthAccountsSection";
import { MFASection } from "@/features/settings/components/MFASection";
import { UserSessionsActivity } from "@/components/settings/UserSessionsActivity";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi } from "@/api";
import { TypoSection, TypoCaption, TypoHeading } from "@/components/shared/Typography";

const tabs = [
  { id: "account", label: "Account", icon: User },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "notifications", label: "Notifications", icon: Bell },
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
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [savingAccount, setSavingAccount] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
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
        <TypoCaption as="p">
          Manage your account settings and preferences
        </TypoCaption>
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
                    ? "bg-primary-soft text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <t.icon size={16} className="shrink-0" />
                {t.label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="min-h-[500px]">
          <Card className="divide-y divide-border">
            {tab === "account" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Profile</TypoHeading>
                  <TypoCaption as="p">
                    Manage your public profile information
                  </TypoCaption>
                </div>

                <div className="rounded-lg border border-border bg-muted/30 p-5 space-y-4">
                  <TypoSection>
                    Profile Media
                  </TypoSection>
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
                        <TypoCaption as="p">
                          Drag & drop or crop before upload
                        </TypoCaption>
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
                        <TypoCaption as="p">
                          3:1 aspect ratio landscape
                        </TypoCaption>
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
                </div>

                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (savingAccount) return;
                    setSavingAccount(true);
                    try {
                      await new Promise((r) => setTimeout(r, 800));
                      toast.success("Profile saved successfully");
                    } finally {
                      setSavingAccount(false);
                    }
                  }}
                  className="space-y-5"
                >
                  <div className="grid gap-5 sm:grid-cols-2">
                    <div>
                      <label className={lbl}>Full name</label>
                      <input
                        className={inp}
                        defaultValue={currentUser.name}
                        placeholder="Your full name"
                      />
                    </div>
                    <div>
                      <label className={lbl}>Username</label>
                      <input
                        className={inp}
                        defaultValue={currentUser.handle}
                        placeholder="username"
                      />
                    </div>
                  </div>
                  <div>
                    <label className={lbl}>Email</label>
                    <input
                      className={inp}
                      defaultValue="nancy@devlink.io"
                      type="email"
                      placeholder="email@example.com"
                    />
                  </div>
                  <div>
                    <label className={lbl}>Bio</label>
                    <textarea
                      rows={3}
                      className={inp}
                      defaultValue="Product engineer. React / Postgres / Rust."
                      placeholder="Tell us about yourself"
                    />
                    <TypoCaption as="p">
                      Brief description for your profile
                    </TypoCaption>
                  </div>
                  <div className="flex items-center gap-3 pt-2">
                    <Button type="submit" className="gap-2" disabled={savingAccount}>
                      <Save size={15} />
                      {savingAccount ? "Saving..." : "Save changes"}
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => toast.success("Changes discarded")}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>

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
                  <TypoCaption as="p">
                    Customize how DevLink looks for you
                  </TypoCaption>
                </div>

                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Theme</p>
                      <TypoCaption as="p">
                        Select your preferred color scheme
                      </TypoCaption>
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
                      <TypoCaption as="p">
                        Minimize animations across the interface
                      </TypoCaption>
                    </div>
                    <Switch />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">Compact mode</p>
                      <TypoCaption as="p">
                        Reduce spacing for a denser layout
                      </TypoCaption>
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
                  <TypoCaption as="p">
                    Choose what notifications you receive
                  </TypoCaption>
                </div>

                <div className="space-y-5">
                  <div>
                    <TypoSection>
                      Push notifications
                    </TypoSection>
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
                    <TypoSection>
                      Email notifications
                    </TypoSection>
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

            {tab === "security" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Security</TypoHeading>
                  <TypoCaption as="p">
                    Manage your password and account security
                  </TypoCaption>
                </div>

                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (savingPassword) return;
                    setSavingPassword(true);
                    try {
                      await new Promise((r) => setTimeout(r, 800));
                      toast.success("Password updated successfully");
                    } finally {
                      setSavingPassword(false);
                    }
                  }}
                  className="max-w-md space-y-5"
                >
                  <div>
                    <label className={lbl}>Current password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? "text" : "password"}
                        className={`${inp} pr-10`}
                        placeholder="Enter current password"
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

                  <div>
                    <label className={lbl}>New password</label>
                    <div className="relative">
                      <input
                        type={showNewPassword ? "text" : "password"}
                        className={`${inp} pr-10`}
                        placeholder="Enter new password"
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

                  <div className="flex gap-3 pt-2">
                    <Button type="submit" disabled={savingPassword} className="gap-2">
                      <Save size={15} />
                      {savingPassword ? "Updating..." : "Update password"}
                    </Button>
                  </div>
                </form>

                <Separator />

                <OAuthAccountsSection />

                <Separator />

                <MFASection />

                <Separator />

                <UserSessionsActivity />
              </div>
            )}

            {tab === "billing" && (
              <div className="p-6 space-y-6">
                <div>
                  <TypoHeading as="h2">Billing</TypoHeading>
                  <TypoCaption as="p">
                    Manage your subscription and payment methods
                  </TypoCaption>
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
                  <TypoCaption as="p">
                    Download a copy of your DevLink data
                  </TypoCaption>
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
