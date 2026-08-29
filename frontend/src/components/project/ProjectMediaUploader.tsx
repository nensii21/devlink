import React, { useState, useRef } from "react";
import {
  UploadCloud,
  X,
  Trash2,
  MoveUp,
  MoveDown,
  Star,
  Video,
  Plus,
  Check,
  Film,
  AlertCircle,
} from "lucide-react";
import { type ProjectMediaItem } from "./ProjectMediaGallery";
import { toast } from "sonner";

export interface ProjectMediaUploaderProps {
  initialCoverImage?: string;
  initialScreenshots?: (string | ProjectMediaItem)[];
  initialVideoDemoUrl?: string;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: {
    coverImage: string;
    screenshots: ProjectMediaItem[];
    videoDemoUrl: string;
  }) => void;
}

export function ProjectMediaUploader({
  initialCoverImage = "",
  initialScreenshots = [],
  initialVideoDemoUrl = "",
  isOpen,
  onClose,
  onSave,
}: ProjectMediaUploaderProps) {
  const [coverImage, setCoverImage] = useState<string>(initialCoverImage);
  const [videoDemoUrl, setVideoDemoUrl] = useState<string>(initialVideoDemoUrl);
  const [screenshots, setScreenshots] = useState<ProjectMediaItem[]>(() => {
    return initialScreenshots.map((item, idx) => {
      if (typeof item === "string") {
        return {
          id: `screenshot-${idx}-${Date.now()}`,
          url: item,
          type: "image" as const,
          title: `Screenshot ${idx + 1}`,
          caption: "",
          order: idx,
        };
      }
      return item;
    });
  });

  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFiles = (files: FileList | File[]) => {
    const validImageFiles = Array.from(files).filter((file) => file.type.startsWith("image/"));

    if (validImageFiles.length === 0) {
      toast.error("Please select valid image files (PNG, JPG, WebP, GIF)");
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);

    const newItems: ProjectMediaItem[] = [];

    validImageFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        newItems.push({
          id: `media-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          url: result,
          type: "image",
          title: file.name.replace(/\.[^/.]+$/, ""),
          caption: "",
          order: screenshots.length + index,
        });

        if (newItems.length === validImageFiles.length) {
          setUploadProgress(100);
          setTimeout(() => {
            setScreenshots((prev) => [...prev, ...newItems]);
            if (!coverImage && newItems.length > 0) {
              setCoverImage(newItems[0].url);
            }
            setIsUploading(false);
            setUploadProgress(0);
            toast.success(`Added ${newItems.length} screenshot(s)`);
          }, 300);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const handleDelete = (id: string) => {
    const itemToDelete = screenshots.find((s) => s.id === id);
    setScreenshots((prev) => prev.filter((s) => s.id !== id));

    // If deleted item was the cover image, pick another or clear
    if (itemToDelete && itemToDelete.url === coverImage) {
      const remaining = screenshots.filter((s) => s.id !== id);
      setCoverImage(remaining.length > 0 ? remaining[0].url : "");
    }
    toast.info("Screenshot removed");
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    setScreenshots((prev) => {
      const copy = [...prev];
      const temp = copy[index - 1];
      copy[index - 1] = copy[index];
      copy[index] = temp;
      return copy.map((item, idx) => ({ ...item, order: idx }));
    });
  };

  const handleMoveDown = (index: number) => {
    if (index === screenshots.length - 1) return;
    setScreenshots((prev) => {
      const copy = [...prev];
      const temp = copy[index + 1];
      copy[index + 1] = copy[index];
      copy[index] = temp;
      return copy.map((item, idx) => ({ ...item, order: idx }));
    });
  };

  const handleSetCover = (url: string) => {
    setCoverImage(url);
    toast.success("Set as project cover image");
  };

  const handleUpdateCaption = (id: string, caption: string) => {
    setScreenshots((prev) => prev.map((s) => (s.id === id ? { ...s, caption } : s)));
  };

  const handleSave = () => {
    onSave({
      coverImage,
      screenshots,
      videoDemoUrl: videoDemoUrl.trim(),
    });
    toast.success("Project media gallery updated successfully!");
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="media-uploader-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in"
      data-testid="project-media-uploader-modal"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border/80 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Film className="h-5 w-5" />
            </div>
            <div>
              <h2 id="media-uploader-title" className="text-base font-semibold text-foreground">
                Manage Project Screenshots & Media
              </h2>
              <p className="text-xs text-muted-foreground">
                Upload screenshots, select cover art, and attach interactive demo videos.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            data-testid="close-uploader-btn"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Content Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Drag and Drop Zone */}
          <div>
            <label className="block text-xs font-semibold text-foreground mb-2">
              Upload Screenshots (Drag & Drop or Browse)
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-primary bg-primary/5 scale-[0.99]"
                  : "border-border/80 bg-muted/20 hover:border-primary/60 hover:bg-muted/40"
              }`}
              data-testid="dropzone-area"
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                className="hidden"
                onChange={handleFileInputChange}
                data-testid="media-file-input"
              />
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                <UploadCloud className="h-5 w-5" />
              </div>
              <p className="text-sm font-medium text-foreground">
                Click to browse or drop screenshots here
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Supports PNG, JPG, WebP, GIF up to 10MB each
              </p>
            </div>

            {isUploading && (
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Uploading files...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Video Demo Input */}
          <div>
            <label
              htmlFor="video-demo-url"
              className="flex items-center gap-1.5 text-xs font-semibold text-foreground mb-1.5"
            >
              <Video className="h-3.5 w-3.5 text-primary" />
              Video Demo Link (YouTube, Vimeo, or MP4 URL)
            </label>
            <input
              id="video-demo-url"
              type="url"
              value={videoDemoUrl}
              onChange={(e) => setVideoDemoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=... or https://example.com/demo.mp4"
              className="w-full rounded-lg border border-border bg-background px-3.5 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              data-testid="video-demo-input"
            />
          </div>

          {/* Uploaded Screenshots List & Reordering */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-foreground">
                Gallery Screenshots ({screenshots.length})
              </span>
              <span className="text-[11px] text-muted-foreground">
                Click star to set as cover image
              </span>
            </div>

            {screenshots.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">
                No screenshots added yet. Upload some images above!
              </div>
            ) : (
              <div className="space-y-2.5" data-testid="screenshots-list">
                {screenshots.map((item, idx) => {
                  const isCover = item.url === coverImage;
                  return (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 rounded-xl border border-border bg-muted/20 p-2.5 transition-all hover:bg-muted/40"
                      data-testid={`screenshot-item-${idx}`}
                    >
                      {/* Image Thumbnail */}
                      <div className="relative h-14 w-20 flex-shrink-0 overflow-hidden rounded-lg border border-border bg-black/80">
                        <img
                          src={item.url}
                          alt={item.title || "Screenshot"}
                          className="h-full w-full object-cover"
                        />
                        {isCover && (
                          <div className="absolute inset-x-0 bottom-0 bg-amber-500 py-0.5 text-center text-[8px] font-bold text-white">
                            Cover
                          </div>
                        )}
                      </div>

                      {/* Item Details / Caption */}
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-medium text-foreground truncate">
                            {item.title || `Screenshot ${idx + 1}`}
                          </p>
                          <span className="text-[10px] text-muted-foreground">#{idx + 1}</span>
                        </div>
                        <input
                          type="text"
                          value={item.caption || ""}
                          onChange={(e) => handleUpdateCaption(item.id, e.target.value)}
                          placeholder="Add a descriptive caption..."
                          className="w-full rounded border border-border/60 bg-background/80 px-2 py-1 text-[11px] text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                          data-testid={`caption-input-${idx}`}
                        />
                      </div>

                      {/* Action Controls: Star/Cover, Move Up, Move Down, Delete */}
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleSetCover(item.url)}
                          className={`rounded-lg p-1.5 transition-colors ${
                            isCover
                              ? "bg-amber-500/10 text-amber-500"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                          title={isCover ? "Current Cover Image" : "Set as Cover Image"}
                          data-testid={`set-cover-btn-${idx}`}
                        >
                          <Star className={`h-4 w-4 ${isCover ? "fill-amber-500" : ""}`} />
                        </button>
                        <button
                          type="button"
                          disabled={idx === 0}
                          onClick={() => handleMoveUp(idx)}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30"
                          title="Move up"
                          data-testid={`move-up-btn-${idx}`}
                        >
                          <MoveUp className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          disabled={idx === screenshots.length - 1}
                          onClick={() => handleMoveDown(idx)}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30"
                          title="Move down"
                          data-testid={`move-down-btn-${idx}`}
                        >
                          <MoveDown className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(item.id)}
                          className="rounded-lg p-1.5 text-red-500 hover:bg-red-500/10 transition-colors"
                          title="Delete screenshot"
                          data-testid={`delete-screenshot-btn-${idx}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-border/80 bg-muted/20 px-6 py-3.5">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>Changes will be saved to your project overview.</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              type="button"
              className="rounded-lg border border-border px-3.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground shadow-sm hover:bg-primary/90"
              data-testid="save-media-btn"
            >
              <Check className="h-3.5 w-3.5" />
              Save Gallery Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
