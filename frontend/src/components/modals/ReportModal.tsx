"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { reportsApi } from "@/api/modules/reports";
import { Flag, ShieldAlert, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetId: string;
  targetType: "user" | "post";
  targetName?: string;
  onSuccess?: () => void;
}

const REPORT_REASONS = [
  "Spam / Misleading",
  "Harassment or Bullying",
  "Inappropriate Content",
  "Impersonation",
  "Hate Speech or Discrimination",
  "Other",
];

export function ReportModal({
  isOpen,
  onClose,
  targetId,
  targetType,
  targetName,
  onSuccess,
}: ReportModalProps) {
  const [selectedReason, setSelectedReason] = useState<string>(REPORT_REASONS[0]);
  const [description, setDescription] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReason || isSubmitting) return;

    setIsSubmitting(true);
    try {
      if (targetType === "user") {
        await reportsApi.reportProfile(targetId, {
          reason: selectedReason,
          description,
        });
        toast.success("Profile report submitted successfully. Our team will review it.");
      } else {
        await reportsApi.reportPost(targetId, {
          reason: selectedReason,
          description,
          post_id: targetId,
        });
        toast.success("Post report submitted successfully. Thank you for keeping DevLink safe!");
      }

      onSuccess?.();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Failed to submit report";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md p-6 bg-card border-border shadow-2xl rounded-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-base font-bold text-foreground">
                Report {targetType === "user" ? "Profile" : "Post"}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Flag {targetName ? <span className="font-semibold text-foreground">{targetName}</span> : targetType} for review by moderation.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          {/* Reason Selection */}
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold text-foreground">
              Reason for reporting
            </Label>
            <div className="space-y-1.5 pt-1">
              {REPORT_REASONS.map((reason) => (
                <button
                  key={reason}
                  type="button"
                  onClick={() => setSelectedReason(reason)}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg text-xs font-medium border transition-all cursor-pointer flex items-center justify-between",
                    selectedReason === reason
                      ? "bg-destructive/10 text-destructive border-destructive/40 shadow-xs"
                      : "bg-surface text-muted-foreground border-border hover:bg-muted hover:text-foreground"
                  )}
                >
                  <span>{reason}</span>
                  {selectedReason === reason && (
                    <span className="h-2 w-2 rounded-full bg-destructive" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Description Textarea */}
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold text-foreground">
              Additional Details (Optional)
            </Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide any context to help our moderation team..."
              rows={3}
              className="bg-surface text-xs leading-relaxed"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border/50">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="text-xs font-semibold bg-destructive text-destructive-foreground hover:opacity-90 transition-opacity gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Submitting...
                </>
              ) : (
                <>
                  <Flag className="h-3.5 w-3.5" /> Submit Report
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
