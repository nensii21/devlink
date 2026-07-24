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