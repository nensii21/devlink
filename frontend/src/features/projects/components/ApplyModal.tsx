import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { uploadCurrentUserResume } from "@/services/profile";
import { getProjectBuilderFlares } from "@/lib/api";
import { useApplyToFlare } from "@/hooks/useApplications";
import { toast } from "sonner";
import { Upload, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { currentUser } from "@/mocks/seed";

export interface ApplyModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export function ApplyModal({ isOpen, onClose, projectId }: ApplyModalProps) {
  const [selectedFlareId, setSelectedFlareId] = useState<string>("");
  const [message, setMessage] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0); // Mock progress if needed

  const { data: flares, isLoading: isLoadingFlares } = useQuery({
    queryKey: ["projectFlares", projectId],
    queryFn: () => getProjectBuilderFlares(projectId as any),
    enabled: isOpen,
  });

  const applyMutation = useApplyToFlare();

  // Reset state when closed
  React.useEffect(() => {
    if (!isOpen) {
      setSelectedFlareId("");
      setMessage("");
      setPortfolioUrl("");
      setResumeFile(null);
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [isOpen]);

  // Pre-select role if there's only one
  React.useEffect(() => {
    if (flares?.length === 1 && !selectedFlareId) {
      setSelectedFlareId(flares[0].id);
    }
  }, [flares, selectedFlareId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setResumeFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFlareId) {
      toast.error("Please select a role to apply for.");
      return;
    }

    try {
      let finalResumeUrl = undefined;

      if (resumeFile) {
        setIsUploading(true);
        // We do a simple mock progress or just await
        const uploadRes = await uploadCurrentUserResume(resumeFile);
        finalResumeUrl = uploadRes.resume_url || uploadRes.resumeUrl || undefined;
        setIsUploading(false);
      }

      await applyMutation.mutateAsync({
        projectId: projectId as any,
        flareId: selectedFlareId as any,
        message,
        portfolioUrl,
        githubUrl,
        resumeUrl: finalResumeUrl,
      });

      onClose();
    } catch (err: any) {
      setIsUploading(false);
      // useApplyToFlare already shows an error toast, but we can catch it here if we need to.
    }
  };

  const openRoles = flares?.filter((f) => f.status === "open") || [];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isUploading && onClose()}>
      <DialogContent className="max-w-md rounded-xl p-6 sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">Apply to Project</DialogTitle>
        </DialogHeader>

        {isLoadingFlares ? (
          <div className="py-8 text-center text-sm text-muted-foreground">Loading roles...</div>
        ) : openRoles.length === 0 ? (
          <div className="py-8 text-center">
            <AlertCircle size={32} className="mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-sm font-medium text-foreground">No Open Roles</p>
            <p className="mt-1 text-xs text-muted-foreground">
              This project is currently not accepting new applications.
            </p>
            <Button className="mt-4 w-full" variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Role</label>
              <select
                required
                value={selectedFlareId}
                onChange={(e) => setSelectedFlareId(e.target.value)}
                className="w-full rounded-md border border-border bg-background p-2 text-sm text-foreground focus:border-primary focus:outline-none"
              >
                <option value="" disabled>
                  Select a role
                </option>
                {openRoles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.role} - {role.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Short Introduction</label>
              <textarea
                required
                rows={3}
                placeholder="Why are you a great fit for this role?"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full rounded-md border border-border bg-background p-2 text-sm text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Portfolio Links</label>
              <input
                type="url"
                placeholder="https://your-portfolio.com"
                value={portfolioUrl}
                onChange={(e) => setPortfolioUrl(e.target.value)}
                className="w-full rounded-md border border-border bg-background p-2 text-sm text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">GitHub Profile</label>
              <input
                type="url"
                placeholder="https://github.com/username"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                className="w-full rounded-md border border-border bg-background p-2 text-sm text-foreground focus:border-primary focus:outline-none"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Resume (PDF)</label>
              <div className="flex items-center gap-3">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                  id="resume-upload"
                />
                <label
                  htmlFor="resume-upload"
                  className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-xs font-medium text-foreground hover:bg-muted"
                >
                  <Upload size={14} /> {resumeFile ? "Change File" : "Upload Resume"}
                </label>
                {resumeFile && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <FileText size={14} className="text-primary" /> {resumeFile.name}
                  </span>
                )}
              </div>
            </div>

            <div className="pt-4 flex items-center justify-end gap-2 border-t border-border mt-6">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={isUploading || applyMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isUploading || applyMutation.isPending}>
                {isUploading
                  ? "Uploading Resume..."
                  : applyMutation.isPending
                    ? "Submitting..."
                    : "Submit Application"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
