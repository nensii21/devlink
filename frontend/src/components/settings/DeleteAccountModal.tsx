import React, { useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface DeleteAccountModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirmDelete: () => Promise<void> | void;
  userEmail?: string;
}

export function DeleteAccountModal({
  open,
  onOpenChange,
  onConfirmDelete,
  userEmail = "user@example.com",
}: DeleteAccountModalProps) {
  const [confirmationInput, setConfirmationInput] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const CONFIRMATION_KEYWORD = "DELETE";

  const isConfirmed = confirmationInput.trim().toUpperCase() === CONFIRMATION_KEYWORD;

  const handleDelete = async () => {
    if (!isConfirmed) return;

    try {
      setIsDeleting(true);
      setError(null);
      await onConfirmDelete();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete account. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = (newOpenState: boolean) => {
    if (!isDeleting) {
      setConfirmationInput("");
      setError(null);
      onOpenChange(newOpenState);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[440px]">
        <DialogHeader className="space-y-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <AlertTriangle size={24} />
          </div>
          <div>
            <DialogTitle className="text-lg font-bold text-foreground">Delete Account</DialogTitle>
            <DialogDescription className="mt-1 text-xs text-muted-foreground">
              This action is permanent and cannot be undone. All your profile data, projects,
              bookmarks, and activity will be erased forever.
            </DialogDescription>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-xs text-destructive">
            <p className="font-semibold">Warning:</p>
            <p className="mt-0.5">
              Account registered as <span className="font-mono font-bold">{userEmail}</span> will be
              permanently removed.
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="confirm-input" className="text-xs font-medium text-foreground block">
              To confirm, type <span className="font-bold select-all">DELETE</span> below:
            </label>
            <input
              id="confirm-input"
              type="text"
              value={confirmationInput}
              onChange={(e) => setConfirmationInput(e.target.value)}
              placeholder="DELETE"
              disabled={isDeleting}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-xs font-mono outline-none focus:border-destructive focus:ring-2 focus:ring-destructive/20 disabled:opacity-50"
            />
          </div>

          {error && <p className="text-xs font-medium text-destructive">{error}</p>}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleClose(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={!isConfirmed || isDeleting}
            className="gap-1.5"
          >
            {isDeleting && <Loader2 size={14} className="animate-spin" />}
            {isDeleting ? "Deleting Account..." : "Permanently Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
