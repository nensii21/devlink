import React, { useState, useEffect, useCallback } from "react";
import {
  Image as ImageIcon,
  Play,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  X,
  ZoomIn,
  ZoomOut,
  Video,
  Film,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface ProjectMediaItem {
  id: string;
  url: string;
  type: "image" | "video";
  title?: string;
  caption?: string;
  isCover?: boolean;
  order?: number;
}

export interface ProjectMediaGalleryProps {
  coverImage?: string;
  screenshots?: (string | ProjectMediaItem)[];
  videoDemoUrl?: string;
  className?: string;
  onManageMedia?: () => void;
  isOwner?: boolean;
}

export function ProjectMediaGallery({
  coverImage,
  screenshots = [],
  videoDemoUrl,
  className,
  onManageMedia,
  isOwner = false,
}: ProjectMediaGalleryProps) {
  // Normalize items into ProjectMediaItem array
  const mediaItems: ProjectMediaItem[] = [];

  if (coverImage) {
    mediaItems.push({
      id: "cover-img",
      url: coverImage,
      type: "image",
      title: "Cover Image",
      isCover: true,
      order: 0,
    });
  }

  if (videoDemoUrl) {
    mediaItems.push({
      id: "video-demo",
      url: videoDemoUrl,
      type: "video",
      title: "Video Demo",
      caption: "Interactive product demo and feature walkthrough",
      order: 1,
    });
  }

  screenshots.forEach((item, index) => {
    if (typeof item === "string") {
      mediaItems.push({
        id: `screenshot-${index}`,
        url: item,
        type: "image",
        title: `Screenshot ${index + 1}`,
        order: mediaItems.length,
      });
    } else {
      mediaItems.push(item);
    }
  });

  // Sort items by order
  mediaItems.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const [activeIndex, setActiveIndex] = useState(0);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  const currentItem = mediaItems[activeIndex] || mediaItems[0];

  const handlePrev = useCallback(() => {
    setActiveIndex((prev) => (prev > 0 ? prev - 1 : mediaItems.length - 1));
    setZoomLevel(1);
  }, [mediaItems.length]);

  const handleNext = useCallback(() => {
    setActiveIndex((prev) => (prev < mediaItems.length - 1 ? prev + 1 : 0));
    setZoomLevel(1);
  }, [mediaItems.length]);

  // Keyboard navigation for lightbox
  useEffect(() => {
    if (!isLightboxOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsLightboxOpen(false);
      } else if (e.key === "ArrowLeft") {
        handlePrev();
      } else if (e.key === "ArrowRight") {
        handleNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isLightboxOpen, handlePrev, handleNext]);

  // Helper to extract YouTube/Vimeo embed URL
  const getEmbedUrl = (url: string): string | null => {
    try {
      if (url.includes("youtube.com/watch")) {
        const videoId = new URL(url).searchParams.get("v");
        return videoId ? `https://www.youtube.com/embed/${videoId}?autoplay=1` : null;
      }
      if (url.includes("youtu.be/")) {
        const videoId = url.split("youtu.be/")[1]?.split("?")[0];
        return videoId ? `https://www.youtube.com/embed/${videoId}?autoplay=1` : null;
      }
      if (url.includes("vimeo.com/")) {
        const videoId = url.split("vimeo.com/")[1]?.split("?")[0];
        return videoId ? `https://player.vimeo.com/video/${videoId}?autoplay=1` : null;
      }
    } catch {
      return null;
    }
    return null;
  };

  if (mediaItems.length === 0) {
    return (
      <div
        className={cn(
          "rounded-xl border border-dashed border-border/80 bg-muted/20 p-8 text-center",
          className,
        )}
      >
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <ImageIcon className="h-6 w-6" />
        </div>
        <h4 className="text-sm font-semibold text-foreground">No media uploaded yet</h4>
        <p className="mt-1 text-xs text-muted-foreground">
          Add screenshots, cover art, and a video demo to showcase this project.
        </p>
        {isOwner && onManageMedia && (
          <button
            onClick={onManageMedia}
            type="button"
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90"
          >
            <ImageIcon className="h-3.5 w-3.5" />
            Upload Screenshots & Demo
          </button>
        )}
      </div>
    );
  }

  const embedUrl = currentItem?.type === "video" ? getEmbedUrl(currentItem.url) : null;

  return (
    <div className={cn("space-y-3", className)} data-testid="project-media-gallery">
      {/* Header with Title & Manage Button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Film className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold tracking-tight text-foreground">
            Project Gallery & Demos
          </h3>
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
            {mediaItems.length} {mediaItems.length === 1 ? "item" : "items"}
          </span>
        </div>
        {isOwner && onManageMedia && (
          <button
            onClick={onManageMedia}
            type="button"
            className="text-xs font-medium text-primary hover:underline"
            data-testid="manage-gallery-btn"
          >
            Manage Gallery
          </button>
        )}
      </div>

      {/* Main Showcase Viewer */}
      <div className="group relative overflow-hidden rounded-xl border border-border/80 bg-black/90 shadow-sm transition-all">
        <div className="relative aspect-video w-full flex items-center justify-center overflow-hidden">
          {currentItem.type === "video" ? (
            embedUrl ? (
              <iframe
                src={embedUrl}
                title={currentItem.title || "Project Video Demo"}
                className="h-full w-full border-0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <video
                src={currentItem.url}
                controls
                className="h-full w-full object-contain"
                poster={coverImage}
              >
                Your browser does not support the video tag.
              </video>
            )
          ) : (
            <img
              src={currentItem.url}
              alt={currentItem.title || "Project Screenshot"}
              className="h-full w-full object-contain transition-transform duration-300"
              loading="lazy"
            />
          )}

          {/* Media Badges */}
          <div className="absolute left-3 top-3 flex items-center gap-1.5 pointer-events-none">
            {currentItem.isCover && (
              <span className="rounded-md bg-amber-500/90 px-2 py-0.5 text-[10px] font-semibold text-white shadow-sm backdrop-blur-sm">
                Cover Image
              </span>
            )}
            {currentItem.type === "video" && (
              <span className="flex items-center gap-1 rounded-md bg-blue-600/90 px-2 py-0.5 text-[10px] font-semibold text-white shadow-sm backdrop-blur-sm">
                <Video className="h-3 w-3" />
                Video Demo
              </span>
            )}
          </div>

          {/* Controls Overlay */}
          <div className="absolute right-3 top-3 flex items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              onClick={() => setIsLightboxOpen(true)}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-black/60 text-white backdrop-blur-sm transition-all hover:bg-black/80 hover:scale-105"
              title="Fullscreen Preview"
              data-testid="open-lightbox-btn"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>

          {/* Navigation Arrows for Main View */}
          {mediaItems.length > 1 && (
            <>
              <button
                onClick={handlePrev}
                className="absolute left-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white opacity-0 backdrop-blur-sm transition-all hover:bg-black/80 group-hover:opacity-100 hover:scale-110"
                aria-label="Previous image"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={handleNext}
                className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white opacity-0 backdrop-blur-sm transition-all hover:bg-black/80 group-hover:opacity-100 hover:scale-110"
                aria-label="Next image"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </>
          )}

          {/* Caption bar */}
          {(currentItem.caption || currentItem.title) && (
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 pt-6 text-white">
              {currentItem.title && <p className="text-xs font-semibold">{currentItem.title}</p>}
              {currentItem.caption && (
                <p className="text-[11px] text-white/80 line-clamp-1">{currentItem.caption}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Thumbnails Row */}
      {mediaItems.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 scrollbar-thin">
          {mediaItems.map((item, idx) => (
            <button
              key={item.id || idx}
              onClick={() => setActiveIndex(idx)}
              className={cn(
                "relative h-16 w-24 flex-shrink-0 overflow-hidden rounded-lg border-2 bg-muted transition-all hover:opacity-90",
                activeIndex === idx
                  ? "border-primary ring-2 ring-primary/20 scale-[1.02]"
                  : "border-border/60 opacity-60 hover:opacity-100",
              )}
              data-testid={`gallery-thumb-${idx}`}
            >
              {item.type === "video" ? (
                <div className="flex h-full w-full items-center justify-center bg-zinc-900 text-white">
                  <Play className="h-5 w-5 fill-white/80 text-white/80" />
                </div>
              ) : (
                <img
                  src={item.url}
                  alt={item.title || `Thumbnail ${idx + 1}`}
                  className="h-full w-full object-cover"
                />
              )}
              {item.isCover && (
                <div className="absolute bottom-1 left-1 rounded bg-amber-500 px-1 text-[8px] font-bold text-white leading-tight">
                  Cover
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Fullscreen Lightbox Modal */}
      {isLightboxOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-md p-4 animate-in fade-in duration-200"
          data-testid="lightbox-modal"
        >
          {/* Top Bar */}
          <div className="absolute top-4 inset-x-4 flex items-center justify-between z-10">
            <div className="text-white">
              <span className="text-xs font-semibold text-white/90">
                {currentItem.title || `Media ${activeIndex + 1} of ${mediaItems.length}`}
              </span>
              <span className="ml-2 text-xs text-white/60">
                ({activeIndex + 1} / {mediaItems.length})
              </span>
            </div>
            <div className="flex items-center gap-2">
              {currentItem.type === "image" && (
                <>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(z + 0.25, 2.5))}
                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20"
                    title="Zoom in"
                  >
                    <ZoomIn className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(z - 0.25, 0.75))}
                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20"
                    title="Zoom out"
                  >
                    <ZoomOut className="h-4 w-4" />
                  </button>
                </>
              )}
              <a
                href={currentItem.url}
                target="_blank"
                rel="noreferrer"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20"
                title="Open original"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
              <button
                onClick={() => setIsLightboxOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20"
                title="Close"
                data-testid="close-lightbox-btn"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Centered Media Content */}
          <div className="relative max-h-[80vh] max-w-[90vw] flex items-center justify-center overflow-hidden">
            {currentItem.type === "video" ? (
              embedUrl ? (
                <div className="aspect-video w-[80vw] max-w-4xl">
                  <iframe
                    src={embedUrl}
                    title="Project Video"
                    className="h-full w-full rounded-xl"
                    allowFullScreen
                  />
                </div>
              ) : (
                <video
                  src={currentItem.url}
                  controls
                  autoPlay
                  className="max-h-[75vh] max-w-full rounded-xl"
                />
              )
            ) : (
              <img
                src={currentItem.url}
                alt={currentItem.title || "Full preview"}
                style={{ transform: `scale(${zoomLevel})` }}
                className="max-h-[75vh] max-w-full object-contain rounded-lg transition-transform duration-150"
              />
            )}
          </div>

          {/* Navigation for Lightbox */}
          {mediaItems.length > 1 && (
            <>
              <button
                onClick={handlePrev}
                className="absolute left-6 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-all"
                aria-label="Previous"
              >
                <ChevronLeft className="h-6 w-6" />
              </button>
              <button
                onClick={handleNext}
                className="absolute right-6 top-1/2 flex h-12 w-12 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-all"
                aria-label="Next"
              >
                <ChevronRight className="h-6 w-6" />
              </button>
            </>
          )}

          {/* Bottom Caption */}
          {currentItem.caption && (
            <div className="absolute bottom-6 inset-x-0 text-center">
              <span className="inline-block rounded-full bg-black/60 px-4 py-1.5 text-xs text-white/90 backdrop-blur-sm">
                {currentItem.caption}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
