import React, { useState, useRef, useCallback } from "react";
import {
  Upload,
  Image as ImageIcon,
  Camera,
  X,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
  FileImage,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { TypoCaption, TypoCard, TypoSection } from "@/components/shared/Typography";
import { MediaCaptureModal } from "./MediaCaptureModal";
import { cn } from "@/lib/utils";

export type MediaUploaderPreset = "avatar" | "banner" | "post" | "organization" | "project" | "default";

export interface ReusableMediaUploaderProps {
  preset?: MediaUploaderPreset;
  value?: string | null;
  onChange?: (url: string | null, file?: File | null) => void;
  onUpload?: (file: File) => Promise<string>;
  maxSizeMB?: number;
  accept?: string;
  aspectRatio?: "1:1" | "16:9" | "4:3" | "free";
  enableCamera?: boolean;
  disabled?: boolean;
  className?: string;
  label?: string;
  description?: string;
}

export function ReusableMediaUploader({
  preset = "default",
  value = null,
  onChange,
  onUpload,
  maxSizeMB = 5,
  accept = "image/jpeg,image/png,image/webp,image/gif",
  aspectRatio = "free",
  enableCamera = true,
  disabled = false,
  className,
  label,
  description,
}: ReusableMediaUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(value || null);
  const [cameraModalOpen, setCameraModalOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Preset configuration defaults
  const presetConfig = {
    avatar: {
      aspect: "rounded-full aspect-square max-w-[140px] max-h-[140px]",
      label: label || "Upload Avatar",
      desc: description || "PNG, JPG up to 5MB",
    },
    banner: {
      aspect: "aspect-[3/1] w-full min-h-[160px]",
      label: label || "Upload Cover Banner",
      desc: description || "Recommended 1200x400 (PNG, JPG up to 10MB)",
    },
    post: {
      aspect: "aspect-[16/9] w-full min-h-[180px]",
      label: label || "Attach Post Image/Video",
      desc: description || "PNG, JPG, GIF or MP4",
    },
    organization: {
      aspect: "aspect-square w-24 h-24 rounded-2xl",
      label: label || "Org Logo",
      desc: description || "Square logo max 5MB",
    },
    project: {
      aspect: "aspect-[16/10] w-full min-h-[180px]",
      label: label || "Project Screenshot / Media",
      desc: description || "High resolution project image",
    },
    default: {
      aspect: "w-full min-h-[160px]",
      label: label || "Drag & drop your file here",
      desc: description || `Supports images up to ${maxSizeMB}MB`,
    },
  }[preset];

  // Helper validation
  const validateFile = (file: File): string | null => {
    // Size check
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return `File size exceeds the ${maxSizeMB}MB limit (${(file.size / (1024 * 1024)).toFixed(1)}MB).`;
    }

    // Mime type check
    const allowedTypes = accept.split(",").map((t) => t.trim().toLowerCase());
    const fileType = file.type.toLowerCase();
    const isAllowed = allowedTypes.some((allowed) => {
      if (allowed.endsWith("/*")) {
        return fileType.startsWith(allowed.replace("/*", ""));
      }
      return fileType === allowed;
    });

    if (!isAllowed && fileType) {
      return `Invalid file type (${file.type}). Supported formats: ${accept}.`;
    }

    return null;
  };

  // Perform upload simulation or custom upload callback
  const processUpload = useCallback(
    async (file: File) => {
      setErrorMessage(null);
      setCurrentFile(file);
      setUploadProgress(10);

      // Local preview
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);

      try {
        let finalUrl = objectUrl;

        if (onUpload) {
          // Progress simulation
          const interval = setInterval(() => {
            setUploadProgress((prev) => (prev && prev < 90 ? prev + 15 : prev));
          }, 150);

          finalUrl = await onUpload(file);
          clearInterval(interval);
        } else {
          // Simulated progress for demonstration
          for (let p = 25; p <= 100; p += 25) {
            await new Promise((r) => setTimeout(r, 80));
            setUploadProgress(p);
          }
        }

        setUploadProgress(100);
        setTimeout(() => setUploadProgress(null), 500);

        if (onChange) {
          onChange(finalUrl, file);
        }
      } catch (err: any) {
        setUploadProgress(null);
        setErrorMessage(err.message || "Upload failed. Please try again.");
      }
    },
    [onUpload, onChange]
  );

  const handleFileChange = (file: File) => {
    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      return;
    }
    processUpload(file);
  };

  // Drag & drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileChange(files[0]);
    }
  };

  const handleRemove = () => {
    setPreviewUrl(null);
    setCurrentFile(null);
    setErrorMessage(null);
    setUploadProgress(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (onChange) onChange(null, null);
  };

  const handleRetry = () => {
    if (currentFile) {
      processUpload(currentFile);
    } else if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className={cn("w-full space-y-2", className)}>
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        disabled={disabled}
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            handleFileChange(e.target.files[0]);
          }
        }}
      />

      {/* Main Upload Drop Zone / Preview Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-all duration-200 overflow-hidden bg-card text-center p-4",
          presetConfig.aspect,
          isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border hover:border-primary/40 hover:bg-surface/50",
          disabled && "opacity-60 cursor-not-allowed pointer-events-none",
          errorMessage && "border-destructive/60 bg-destructive/5"
        )}
      >
        {/* Preview State */}
        {previewUrl && !errorMessage ? (
          <div className="relative w-full h-full min-h-[140px] group flex items-center justify-center">
            <img
              src={previewUrl}
              alt="Media preview"
              className={cn(
                "object-cover w-full h-full rounded-xl transition-all duration-300",
                preset === "avatar" && "rounded-full"
              )}
            />

            {/* Progress Overlay */}
            {uploadProgress !== null && (
              <div className="absolute inset-0 bg-black/60 backdrop-blur-xs flex flex-col items-center justify-center p-4 text-white z-20">
                <Loader2 className="h-6 w-6 animate-spin mb-2 text-primary" />
                <TypoCaption className="text-xs font-semibold text-white">
                  Uploading... {uploadProgress}%
                </TypoCaption>
                <div className="w-3/4 max-w-[200px] h-1.5 bg-white/20 rounded-full mt-2 overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-200 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Hover Actions Overlay */}
            {uploadProgress === null && (
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-2 rounded-xl z-10">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="h-8 text-xs gap-1.5 bg-white/90 text-foreground hover:bg-white"
                >
                  <RefreshCw size={13} /> Replace
                </Button>

                {enableCamera && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setCameraModalOpen(true)}
                    className="h-8 text-xs gap-1.5 bg-white/90 text-foreground hover:bg-white"
                  >
                    <Camera size={13} /> Camera
                  </Button>
                )}

                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={handleRemove}
                  className="h-8 text-xs gap-1.5"
                >
                  <Trash2 size={13} /> Remove
                </Button>
              </div>
            )}
          </div>
        ) : (
          /* Empty / Upload Trigger State */
          <div className="flex flex-col items-center justify-center p-4 space-y-3">
            <div className="p-3 rounded-full bg-primary-soft text-primary">
              <Upload size={22} />
            </div>

            <div>
              <TypoCard className="text-sm font-semibold text-foreground">
                {presetConfig.label}
              </TypoCard>
              <TypoCaption className="text-xs mt-0.5 text-muted-foreground block">
                {presetConfig.desc}
              </TypoCaption>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="h-8 text-xs gap-1.5 shadow-2xs"
              >
                <FileImage size={14} /> Browse File
              </Button>

              {enableCamera && (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setCameraModalOpen(true)}
                  className="h-8 text-xs gap-1.5 shadow-2xs"
                >
                  <Camera size={14} /> Take Photo
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Error Banner & Retry Trigger */}
      {errorMessage && (
        <div className="flex items-center justify-between rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
          <div className="flex items-center gap-2">
            <AlertCircle size={15} className="shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleRetry}
            className="h-7 text-xs text-destructive hover:bg-destructive/10 gap-1"
          >
            <RefreshCw size={12} /> Retry
          </Button>
        </div>
      )}

      {/* Webcam / Device Camera Capture Modal Integration */}
      {enableCamera && (
        <MediaCaptureModal
          open={cameraModalOpen}
          onClose={() => setCameraModalOpen(false)}
          onUpload={(file) => {
            handleFileChange(file);
            setCameraModalOpen(false);
          }}
          title={`Capture ${preset !== "default" ? preset : "Image"}`}
        />
      )}
    </div>
  );
}

export default ReusableMediaUploader;
