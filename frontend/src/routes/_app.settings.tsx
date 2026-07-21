import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { DeleteAccountModal } from "@/components/settings/DeleteAccountModal";
import { Trash2 } from "lucide-react";

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