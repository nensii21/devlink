import { useEffect, useMemo, useRef, useState } from "react";
import { Card } from "@/components/shared/primitives";
import { FileText, Upload, XCircle } from "lucide-react";
import { uploadCurrentUserResume } from "@/services/profile";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export interface ResumeUploadCardProps {
  resumeUrl?: string | null;
  editable?: boolean;
}

export function ResumeUploadCard({ resumeUrl, editable = false }: ResumeUploadCardProps) {
  const [currentResumeUrl, setCurrentResumeUrl] = useState<string | null>(resumeUrl ?? null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setCurrentResumeUrl(resumeUrl ?? null);
  }, [resumeUrl]);

  const handleFileSelection = async (file: File | null) => {
    if (!file) return;

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("Resume file must be smaller than 5MB.");
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      const uploadedUrl = await uploadCurrentUserResume(file);
      setCurrentResumeUrl(uploadedUrl.resume_url ?? uploadedUrl.resumeUrl ?? null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to upload resume right now.";
      setError(message);
    } finally {
      setIsUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  };

  const dropState = useMemo(() => {
    if (!editable) {
      return "View uploaded résumé";
    }

    if (isUploading) {
      return "Uploading...";
    }

    return currentResumeUrl ? "Replace resume" : "Upload resume";
  }, [currentResumeUrl, editable, isUploading]);

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    await handleFileSelection(event.dataTransfer.files?.[0] ?? null);
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <FileText size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Resume</h2>
            <p className="text-xs text-muted-foreground">PDF uploads only · max 5MB</p>
          </div>
        </div>
        {editable ? (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-md border border-border bg-background px-3 py-2 text-[13px] font-semibold text-foreground hover:bg-muted"
          >
            {currentResumeUrl ? "Replace" : "Upload"}
          </button>
        ) : null}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(event) => handleFileSelection(event.target.files?.[0] ?? null)}
      />

      <div
        className={`mt-4 rounded-lg border border-dashed p-4 transition-colors ${isDragging ? "border-primary bg-primary/5" : "border-border bg-muted/30"}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {currentResumeUrl ? (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-foreground">Resume ready to share</p>
              <p className="text-xs text-muted-foreground">Your latest PDF is attached to this profile.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <a
                href={currentResumeUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90"
              >
                View Resume
              </a>
              {editable ? (
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="rounded-md border border-border bg-background px-3 py-2 text-[13px] font-semibold text-foreground hover:bg-muted"
                >
                  Replace
                </button>
              ) : null}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Upload size={16} />
              <span>{dropState}</span>
            </div>
            <p className="text-sm text-muted-foreground">No resume uploaded</p>
            {editable ? (
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="w-fit rounded-md border border-border bg-background px-3 py-2 text-[13px] font-semibold text-foreground hover:bg-muted"
              >
                Choose PDF
              </button>
            ) : null}
          </div>
        )}
      </div>

      {isUploading ? <p className="mt-3 text-sm text-muted-foreground">Uploading your resume…</p> : null}
      {error ? (
        <div className="mt-3 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-600">
          <XCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}
    </Card>
  );
}

export default ResumeUploadCard;
