"use client";

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/shared/primitives";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { applicationsApi, type ApplicationPrefillData } from "@/api/modules/applications";
import { toast } from "sonner";
import {
  Sparkles,
  Github,
  Globe,
  FileText,
  CheckCircle2,
  Zap,
  Loader2,
  User,
  Briefcase,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface OneClickApplyModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectTitle: string;
  availableRoles?: string[];
  flareId?: string;
  onSuccess?: () => void;
}

export function OneClickApplyModal({
  isOpen,
  onClose,
  projectId,
  projectTitle,
  availableRoles = ["Frontend Developer", "Backend Engineer", "Full Stack Developer", "UI/UX Designer"],
  flareId,
  onSuccess,
}: OneClickApplyModalProps) {
  const [prefill, setPrefill] = useState<ApplicationPrefillData | null>(null);
  const [isLoadingPrefill, setIsLoadingPrefill] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [selectedRole, setSelectedRole] = useState<string>(availableRoles[0] || "Developer");
  const [coverLetter, setCoverLetter] = useState<string>("");
  const [resumeUrl, setResumeUrl] = useState<string>("");
  const [portfolioUrl, setPortfolioUrl] = useState<string>("");
  const [githubUrl, setGithubUrl] = useState<string>("");

  useEffect(() => {
    if (isOpen) {
      fetchPrefillData();
    }
  }, [isOpen]);

  const fetchPrefillData = async () => {
    setIsLoadingPrefill(true);
    try {
      const data = await applicationsApi.getPrefill();
      setPrefill(data);
      if (data.role && availableRoles.includes(data.role)) {
        setSelectedRole(data.role);
      }
      if (data.suggested_cover_letter) {
        setCoverLetter(data.suggested_cover_letter);
      }
      if (data.resume_url) setResumeUrl(data.resume_url);
      if (data.portfolio_url) setPortfolioUrl(data.portfolio_url);
      if (data.github_url) setGithubUrl(data.github_url);
    } catch (e) {
      console.warn("Could not load prefill data:", e);
    } finally {
      setIsLoadingPrefill(false);
    }
  };

  const handleAutoGenerateCoverLetter = () => {
    if (prefill?.suggested_cover_letter) {
      setCoverLetter(prefill.suggested_cover_letter);
      toast.success("Cover letter generated from your DevLink profile!");
    } else {
      const fallback = `Hi! I'm applying for the ${selectedRole} position on ${projectTitle}. I'm excited to contribute my software engineering skills and build great software together.`;
      setCoverLetter(fallback);
      toast.success("Default cover letter generated!");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);
    try {
      await applicationsApi.oneClickApply({
        project_id: projectId,
        flare_id: flareId,
        selected_role: selectedRole,
        cover_letter: coverLetter,
        resume_url: resumeUrl || prefill?.resume_url,
        portfolio_url: portfolioUrl || prefill?.portfolio_url,
        github_url: githubUrl || prefill?.github_url,
        auto_use_profile: true,
      });

      toast.success("Application submitted in 1-Click! 🚀");
      onSuccess?.();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Failed to submit application";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg sm:max-w-xl p-6 bg-card border-border shadow-2xl rounded-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Zap className="h-5 w-5 fill-primary/20" />
            </div>
            <div>
              <DialogTitle className="text-lg font-bold text-foreground">
                1-Click Application
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Apply to <span className="font-semibold text-foreground">{projectTitle}</span> using your DevLink profile.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {isLoadingPrefill ? (
          <div className="flex flex-col items-center justify-center py-10 space-y-3">
            <Loader2 className="h-7 w-7 animate-spin text-primary" />
            <TypoCaption className="text-xs text-muted-foreground">
              Loading your DevLink profile details…
            </TypoCaption>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 mt-2">
            {/* DevLink Profile Quick Sync Banner */}
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-3.5 flex items-start gap-3">
              <User className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="text-xs space-y-0.5">
                <p className="font-semibold text-foreground">
                  {prefill?.full_name || "DevLink Developer"} (@{prefill?.username || "dev"})
                </p>
                <p className="text-muted-foreground">
                  {prefill?.headline || "Software Developer"} • {prefill?.skills?.length || 0} verified skills
                </p>
              </div>
            </div>

            {/* Role Selection */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-muted-foreground" /> Applying as Role
              </Label>
              <div className="flex flex-wrap gap-2 pt-1">
                {availableRoles.map((role) => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setSelectedRole(role)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer",
                      selectedRole === role
                        ? "bg-primary text-primary-foreground border-primary shadow-xs"
                        : "bg-surface text-muted-foreground border-border hover:text-foreground"
                    )}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>

            {/* DevLink Profile Integration Badges */}
            <div className="grid grid-cols-3 gap-2 pt-1">
              {/* GitHub */}
              <div className="rounded-lg border border-border bg-surface p-2.5 flex flex-col justify-between text-xs">
                <div className="flex items-center gap-1.5 text-muted-foreground font-medium mb-1">
                  <Github className="h-3.5 w-3.5" /> GitHub
                </div>
                {githubUrl ? (
                  <span className="text-[11px] font-semibold text-emerald-500 flex items-center gap-1 truncate">
                    <CheckCircle2 className="h-3 w-3 shrink-0" /> Verified
                  </span>
                ) : (
                  <span className="text-[11px] text-muted-foreground">Not linked</span>
                )}
              </div>

              {/* Portfolio */}
              <div className="rounded-lg border border-border bg-surface p-2.5 flex flex-col justify-between text-xs">
                <div className="flex items-center gap-1.5 text-muted-foreground font-medium mb-1">
                  <Globe className="h-3.5 w-3.5" /> Portfolio
                </div>
                {portfolioUrl ? (
                  <span className="text-[11px] font-semibold text-emerald-500 flex items-center gap-1 truncate">
                    <CheckCircle2 className="h-3 w-3 shrink-0" /> Linked
                  </span>
                ) : (
                  <span className="text-[11px] text-muted-foreground">Not linked</span>
                )}
              </div>

              {/* Resume */}
              <div className="rounded-lg border border-border bg-surface p-2.5 flex flex-col justify-between text-xs">
                <div className="flex items-center gap-1.5 text-muted-foreground font-medium mb-1">
                  <FileText className="h-3.5 w-3.5" /> Resume
                </div>
                {resumeUrl ? (
                  <span className="text-[11px] font-semibold text-emerald-500 flex items-center gap-1 truncate">
                    <CheckCircle2 className="h-3 w-3 shrink-0" /> Attached
                  </span>
                ) : (
                  <span className="text-[11px] text-muted-foreground">Not uploaded</span>
                )}
              </div>
            </div>

            {/* Cover Letter Field + Auto AI Generator */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-semibold text-foreground">
                  Cover Letter / Intro
                </Label>
                <button
                  type="button"
                  onClick={handleAutoGenerateCoverLetter}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline cursor-pointer"
                >
                  <Sparkles className="h-3 w-3" /> Auto-fill from Profile
                </button>
              </div>
              <Textarea
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
                placeholder="Write a brief cover letter or why you're a great fit…"
                rows={3}
                className="bg-surface text-xs leading-relaxed"
              />
            </div>

            {/* Modal Actions */}
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
                className="text-xs font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Submitting…
                  </>
                ) : (
                  <>
                    <Zap className="h-3.5 w-3.5 fill-primary-foreground/20" /> Submit Application (1-Click)
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
