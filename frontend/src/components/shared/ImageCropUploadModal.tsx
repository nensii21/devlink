import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Upload, Image as ImageIcon, AlertCircle, CheckCircle2, Camera } from "lucide-react";
import { toast } from "sonner";
import { uploadImage } from "@/services/imageUpload";
import { cn } from "@/lib/utils";
import { TypoCaption } from "@/components/shared/Typography";

import { CameraCapture } from "@/components/shared/CameraCapture";
import { ImageCropper, ImageCropperHandle, CROP_PRESETS } from "@/components/shared/ImageCropper";

export type ImageCropMode = "avatar" | "banner";

export interface ImageCropUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (url: string) => void;
  mode?: ImageCropMode;
  maxSizeMB?: number;
  title?: string;
}

const MAX_FILE_SIZE_DEFAULT_MB = 5;

export function ImageCropUploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  mode = "avatar",
  maxSizeMB = MAX_FILE_SIZE_DEFAULT_MB,
  title,
}: ImageCropUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);

  // Progress state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cropperRef = useRef<ImageCropperHandle | null>(null);

  const cropPreset = CROP_PRESETS[mode === "banner" ? "banner" : "avatar"];
  const modalTitle = title ?? (mode === "banner" ? "Upload Banner Image" : "Upload Avatar Image");

  // Reset state when modal opens/closes.
  //
  // This used to also call setZoom / setRotation / setPanX / setPanY. None of
  // them exist here -- that state belongs to ImageCropper, which owns it and is
  // reached through cropperRef -- so the effect threw ReferenceError on the
  // first render, and the guard is `!isOpen`, which is true on mount. A modal
  // that is rendered closed took the throwing branch before anyone could open
  // it (#1347).
  //
  // Nothing replaces them: clearing previewUrl below unmounts ImageCropper,
  // which takes its crop state with it, and the cropper re-centres on every
  // `src` load regardless.
  useEffect(() => {
    if (!isOpen) {
      setSelectedFile(null);
      setPreviewUrl(null);
      setError(null);
      setIsCameraActive(false);
      setIsUploading(false);
      setUploadProgress(0);
      setUploadComplete(false);
    }
  }, [isOpen]);

  const validateAndLoadFile = useCallback(
    (file: File) => {
      setError(null);
      if (!file.type.startsWith("image/")) {
        setError("Please select a valid image file (.jpg, .png, .webp, .gif).");
        return;
      }

      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File size exceeds the maximum allowed size of ${maxSizeMB}MB.`);
        return;
      }

      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          setPreviewUrl(reader.result);
        }
      };
      reader.readAsDataURL(file);
    },
    [maxSizeMB],
  );

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
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

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndLoadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndLoadFile(e.target.files[0]);
    }
  };

  // Render the cropper canvas to blob and upload
  const handleUpload = async () => {
    const blob = await cropperRef.current?.getCropBlob();
    if (!blob) {
      setError("Failed to process cropped image.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);
    setError(null);

    try {
      const result = await uploadImage(blob, `cropped-${mode}.webp`, (percent) => {
        setUploadProgress(percent);
      });

      setUploadProgress(100);
      setUploadComplete(true);
      toast.success("Image uploaded successfully!");

      setTimeout(() => {
        onUploadSuccess(result.url);
        onClose();
      }, 400);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to upload image.";
      setError(msg);
      toast.error(msg);
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isUploading && onClose()}>
      <DialogContent className="max-w-xl rounded-xl border border-border bg-card p-6 shadow-xl sm:max-w-2xl">
        <DialogHeader className="pb-2">
          <DialogTitle className="text-xl font-bold tracking-tight text-foreground">
            {modalTitle}
          </DialogTitle>
        </DialogHeader>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Upload State / Dropzone vs Canvas View */}

        {isCameraActive ? (
          <CameraCapture
            onCapture={(file) => {
              setIsCameraActive(false);
              validateAndLoadFile(file);
            }}
            onCancel={() => setIsCameraActive(false)}
          />
        ) : !previewUrl ? (
          <div className="flex flex-col gap-4">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer text-center",
                isDragging
                  ? "border-primary bg-primary/10"
                  : "border-border bg-muted/30 hover:border-primary/60 hover:bg-muted/50",
              )}
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Upload size={24} />
              </div>
              <p className="mt-3 text-sm font-medium text-foreground">
                Drag & drop your image here, or{" "}
                <span className="text-primary underline">browse</span>
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Supports JPEG, PNG, WebP, GIF · Max {maxSizeMB}MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                data-testid="file-input"
                accept="image/jpeg,image/png,image/webp,image/gif"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-border"></div>
              <span className="shrink-0 px-4 text-xs text-muted-foreground uppercase tracking-wider">
                or
              </span>
              <div className="flex-grow border-t border-border"></div>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full h-12 gap-2 rounded-xl"
              onClick={() => setIsCameraActive(true)}
            >
              <Camera size={18} />
              Take a Photo
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Reusable Cropper */}
            {previewUrl && (
              <ImageCropper
                ref={cropperRef}
                src={previewUrl}
                shape={cropPreset.shape}
                aspectRatio={cropPreset.aspectRatio}
                outputWidth={cropPreset.outputWidth}
                previewClassName={cropPreset.shape === "square" ? "rounded-full" : undefined}
              />
            )}

            {/* Upload Progress Indicator Bar */}
            {(isUploading || uploadComplete) && (
              <div className="space-y-2 rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-foreground">
                    {uploadComplete ? (
                      <>
                        <CheckCircle2 size={15} className="text-emerald-500" />
                        <span>Upload complete!</span>
                      </>
                    ) : (
                      <>
                        <ImageIcon size={15} className="text-primary animate-pulse" />
                        <span>Uploading image...</span>
                      </>
                    )}
                  </span>
                  <span className="font-mono text-muted-foreground">{uploadProgress}%</span>
                </div>

                {/* Progress Bar Container */}
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn(
                      "h-full transition-all duration-300 ease-out",
                      uploadComplete ? "bg-emerald-500" : "bg-primary",
                    )}
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="mt-4 gap-2 sm:gap-0">
          {previewUrl && !isUploading && !uploadComplete && (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setPreviewUrl(null);
                setSelectedFile(null);
              }}
              className="mr-auto text-xs"
            >
              Choose different file
            </Button>
          )}

          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isUploading}
            className="text-xs"
          >
            Cancel
          </Button>

          {previewUrl && !uploadComplete && (
            <Button
              type="button"
              onClick={handleUpload}
              disabled={isUploading || !selectedFile}
              className="text-xs font-medium"
            >
              {isUploading ? "Uploading..." : "Crop & Save Image"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
