import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";

import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { Trash2 } from "lucide-react";

import { useState, useCallback } from "react";
import { Eye, EyeOff, Download } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { currentUser } from "@/mocks/seed";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { exportApi } from "@/api";

const tabs = ["Account", "Appearance", "Notifications", "Security", "Billing", "Export"] as const;
type Tab = (typeof tabs)[number];


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

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  const handleConfirmDelete = async () => {
    // Simulate API request to delete account
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    // Redirect to home or logout after deletion
    window.location.href = "/";
  };

  const [tab, setTab] = useState<Tab>("Account");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [savingAccount, setSavingAccount] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [exporting, setExporting] = useState(false);
  const inp =
    "w-full rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";
  const lbl = "mb-1 block text-[13px] font-semibold text-foreground";

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-[22px] font-bold tracking-tight text-foreground">
          Account Settings
        </h1>
        <p className="text-[13px] text-muted-foreground">
          Manage your account preferences and data.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)]">
        <Card className="p-2">
          <nav>
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "flex w-full items-center rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
                  tab === t ? "bg-primary-soft text-primary" : "text-foreground/80 hover:bg-muted",
                )}
              >
                {t}
              </button>
            ))}
          </nav>
        </Card>

        <Card className="p-6">
          <p className="text-[15px] font-semibold text-foreground">{tab}</p>
          <div className="mt-4 space-y-4">
            {tab === "Account" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  toast.success("Saved");
                }}
                className="space-y-4"
              >
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Full name</label>
                    <input className={inp} defaultValue={currentUser.name} />
                  </div>
                  <div>
                    <label className={lbl}>Username</label>
                    <input className={inp} defaultValue={currentUser.handle} />
                  </div>
                </div>
                <div>
                  <label className={lbl}>Email</label>
                  <input className={inp} defaultValue="nancy@devlink.io" />
                </div>
                <div>
                  <label className={lbl}>Bio</label>
                  <textarea
                    rows={3}
                    className={inp}
                    defaultValue="Product engineer. React / Postgres / Rust."
                  />
                </div>
                <button className="rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
                  Save changes
                </button>
              </form>
            )}
            {tab === "Appearance" && (
              <div className="space-y-3 text-[13px] text-foreground">
                <p>
                  Theme: <span className="font-semibold">Light</span> (matches your auth screen).
                </p>
                <p className="text-muted-foreground">Dark mode coming soon.</p>
              </div>
            )}
            {tab === "Notifications" && (
              <div className="space-y-3 text-[13px] text-foreground">
                {[
                  "Direct messages",
                  "Builder requests",
                  "Project mentions",
                  "Hackathon deadlines",
                ].map((n) => (
                  <label
                    key={n}
                    className="flex items-center justify-between border-b border-border pb-3"
                  >
                    <span>{n}</span>
                    <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
                  </label>
                ))}


      {/* DANGER ZONE */}
      <Card className="p-5 border-destructive/30 bg-destructive/5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-destructive flex items-center gap-1.5">
              <Trash2 size={16} /> Danger Zone
            </h3>
            <p className="text-xs text-muted-foreground">
              Permanently delete your account and all associated data. This action cannot be reversed.
            </p>

                <div>
                  <label className={lbl}>New password</label>
                  <div className="relative">
                    <input
                      type={showNewPassword ? "text" : "password"}
                      className={`${inp} pr-10`}
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

                <LoadingButton type="submit" loading={savingPassword} loadingText="Updating...">
                  Update password
                </LoadingButton>
              </form>
            )}
            {tab === "Billing" && (
              <div className="rounded-md border border-primary/30 bg-primary-soft p-4 text-[13px] text-foreground">
                You're on the <span className="font-semibold">Pro</span> plan. Next invoice on Nov
                4, 2026.
              </div>
            )}
            {tab === "Export" && (
              <div className="space-y-4">
                <div>
                  <label className={lbl}>Current password</label>
                  <input type="password" className={inp} />
                </div>
                <div>
                  <label className={lbl}>New password</label>
                  <input type="password" className={inp} />
                </div>
                <button className="rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90">
                  Update password
                </button>
              </div>
            )}
            {tab === "Billing" && (
              <div className="rounded-md border border-primary/30 bg-primary-soft p-4 text-[13px] text-foreground">
                You're on the <span className="font-semibold">Pro</span> plan. Next invoice on Nov
                4, 2026.
                <p className="text-[13px] text-muted-foreground">
                  Download a complete copy of your DevLink data. This includes your profile, skills,
                  projects, connections, messages, bookmarks, and activity history.
                </p>
                <div className="rounded-md border border-border p-4">
                  <h3 className="text-[14px] font-semibold text-foreground">Export your data</h3>
                  <p className="mt-1 text-[12px] text-muted-foreground">
                    Your data will be exported as a JSON file.
                  </p>
                  <LoadingButton
                    className="mt-3"
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
                      } catch (err) {
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
        userEmail="nancy@example.com"
      />
    </div>
  );
}