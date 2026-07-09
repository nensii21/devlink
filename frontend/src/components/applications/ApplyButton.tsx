"use client";

import { useState } from "react";
import { toast } from "sonner";
import { applyToFlare, type UUID } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { cn } from "@/lib/utils";
import { Loader2, Link as LinkIcon } from "lucide-react";

export function ApplyButton({
  flareId,
  projectId,
  className,
}: {
  flareId: UUID;
  projectId: UUID;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");

  const [submitting, setSubmitting] = useState(false);

  async function onSubmit() {
    if (submitting) return;
    setSubmitting(true);
    try {
      await applyToFlare(flareId, projectId, {
        message: message.trim() ? message.trim() : undefined,
        portfolio_url: portfolioUrl.trim() ? portfolioUrl.trim() : undefined,
        github_url: githubUrl.trim() ? githubUrl.trim() : undefined,
      });

      toast.success("Applied successfully");
      setOpen(false);
      setMessage("");
      setPortfolioUrl("");
      setGithubUrl("");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to apply";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={cn("w-full", className)}>
      {open ? (
        <Card className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[13px] font-semibold text-foreground">Apply to this flare</p>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-[12px] font-medium text-muted-foreground hover:text-foreground"
                aria-label="Close apply form"
              >
                Close
              </button>
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Message</Label>
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Why are you a great fit? (optional)"
                rows={4}
                className="bg-surface"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Portfolio URL</Label>
                <Input
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  placeholder="https://..."
                  className="bg-surface"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">GitHub URL</Label>
                <Input
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/..."
                  className="bg-surface"
                />
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
                <LinkIcon size={14} />
                <span>Links optional</span>
              </div>

              <Button
                onClick={onSubmit}
                disabled={submitting}
                className="inline-flex items-center gap-1.5"
              >
                {submitting ? <Loader2 size={16} className="animate-spin" /> : "Submit application"}
              </Button>
            </div>

            {message.trim().length === 0 &&
              portfolioUrl.trim().length === 0 &&
              githubUrl.trim().length === 0 && (
                <p className="text-[11px] text-muted-foreground">
                  Tip: add a message or links to improve your chances.
                </p>
              )}
          </div>
        </Card>
      ) : (
        <Button
          variant="outline"
          className={cn("w-full justify-center", className)}
          onClick={() => setOpen(true)}
        >
          Apply
        </Button>
      )}
    </div>
  );
}
