import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { RotateCw, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";

export type CropShape = "square" | "circle" | "banner";

export interface CropPreset {
  shape: CropShape;
  aspectRatio: number;
  /** Width in logical px used for the exported crop. */
  outputWidth: number;
}

export const CROP_PRESETS: Record<string, CropPreset> = {
  avatar: { shape: "circle", aspectRatio: 1, outputWidth: 400 },
  "org-logo": { shape: "square", aspectRatio: 1, outputWidth: 256 },
  banner: { shape: "banner", aspectRatio: 3, outputWidth: 600 },
  "project-cover": { shape: "banner", aspectRatio: 16 / 9, outputWidth: 768 },
};

const DEFAULT_PRESETS: Record<CropShape, CropPreset> = {
  square: { shape: "square", aspectRatio: 1, outputWidth: 400 },
  circle: { shape: "circle", aspectRatio: 1, outputWidth: 400 },
  banner: { shape: "banner", aspectRatio: 3, outputWidth: 600 },
};

export interface ImageCropperHandle {
  /** Renders the current crop state to a WebP blob. Returns null if no image is loaded. */
  getCropBlob: () => Promise<Blob | null>;
  reset: () => void;
  rotate: () => void;
}

export interface ImageCropperProps {
  src: string;
  shape?: CropShape;
  /** Overrides the output aspect ratio (banner defaults to 3/1, square & circle to 1/1). */
  aspectRatio?: number;
  /** Width in logical px used for the exported crop. Defaults per shape. */
  outputWidth?: number;
  maxZoom?: number;
  /** Renders the built-in responsive zoom/rotate/reset control bar. Default: true. */
  showControls?: boolean;
  /** Additional classes for the crop preview container (e.g. rounded-full for avatars). */
  previewClassName?: string;
  className?: string;
}

/**
 * Reusable canvas-based image cropper.
 *
 * Supports square, circle and banner crop shapes with zoom, rotate, pan and
 * reset controls. The cropped result is available through the imperative
 * `getCropBlob()` handle, so the component can be embedded anywhere (avatar,
 * banner, organization logo, project cover, ...).
 */
export const ImageCropper = forwardRef<ImageCropperHandle, ImageCropperProps>(function ImageCropper(
  {
    src,
    shape = "square",
    aspectRatio,
    outputWidth,
    maxZoom = 3,
    showControls = true,
    previewClassName,
    className,
  },
  ref,
) {
  const preset = DEFAULT_PRESETS[shape];
  const ratio = aspectRatio ?? preset.aspectRatio;
  const width = outputWidth ?? preset.outputWidth;

  const [zoom, setZoom] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [panX, setPanX] = useState<number>(0);
  const [panY, setPanY] = useState<number>(0);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragState = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(
    null,
  );

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const canvasWidth = width;
    const canvasHeight = Math.round(canvasWidth / ratio);

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    ctx.save();

    if (shape === "circle") {
      ctx.beginPath();
      ctx.arc(canvasWidth / 2, canvasHeight / 2, canvasHeight / 2, 0, Math.PI * 2);
      ctx.clip();
    }

    const centerX = canvasWidth / 2 + panX;
    const centerY = canvasHeight / 2 + panY;
    ctx.translate(centerX, centerY);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.scale(zoom, zoom);

    const imgAspect = img.width / img.height;
    let drawW = canvasWidth;
    let drawH = canvasWidth / imgAspect;

    if (drawH < canvasHeight) {
      drawH = canvasHeight;
      drawW = canvasHeight * imgAspect;
    }

    ctx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH);
    ctx.restore();
  }, [ratio, shape, width, panX, panY, rotation, zoom]);

  // Load the image whenever `src` changes.
  useEffect(() => {
    let cancelled = false;
    const img = new Image();
    img.onload = () => {
      if (cancelled) return;
      imageRef.current = img;
      setZoom(1);
      setRotation(0);
      setPanX(0);
      setPanY(0);
    };
    img.src = src;
    return () => {
      cancelled = true;
      imageRef.current = null;
    };
  }, [src]);

  // Redraw when the crop state changes.
  useEffect(() => {
    if (imageRef.current) {
      drawCanvas();
    }
  }, [zoom, rotation, panX, panY, drawCanvas]);

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    dragState.current = { startX: e.clientX, startY: e.clientY, panX, panY };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const drag = dragState.current;
    if (!drag) return;
    setPanX(drag.panX + (e.clientX - drag.startX));
    setPanY(drag.panY + (e.clientY - drag.startY));
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    dragState.current = null;
    (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.05 : 0.05;
    setZoom((prev) => Math.min(maxZoom, Math.max(1, Number((prev + delta).toFixed(2)))));
  };

  const reset = useCallback(() => {
    setZoom(1);
    setRotation(0);
    setPanX(0);
    setPanY(0);
  }, []);

  const rotate = useCallback(() => {
    setRotation((prev) => (prev + 90) % 360);
  }, []);

  useImperativeHandle(ref, () => ({
    getCropBlob: () => {
      const canvas = canvasRef.current;
      if (!canvas) return Promise.resolve(null);
      return new Promise((resolve) => canvas.toBlob(resolve, "image/webp", 0.9));
    },
    reset,
    rotate,
  }));

  return (
    <div className={cn("w-full space-y-3", className)}>
      <div
        className={cn(
          "relative flex justify-center overflow-hidden rounded-xl border border-border bg-black/90 p-4",
        )}
      >
        <div
          className={cn(
            "relative overflow-hidden border-2 border-primary/50 shadow-md",
            shape === "circle" ? "rounded-full" : "rounded-lg",
            previewClassName,
          )}
          style={{
            width: shape === "banner" ? "100%" : "min(100%, 240px)",
            maxWidth: "100%",
            maxHeight: shape === "banner" ? "min(100%, 180px)" : "240px",
            aspectRatio: `${ratio}`,
          }}
        >
          <canvas
            ref={canvasRef}
            data-testid="cropper-canvas"
            className="block h-full w-full cursor-grab touch-none select-none object-contain active:cursor-grabbing"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerUp}
            onWheel={handleWheel}
          />
        </div>
      </div>

      {showControls && (
        <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-3">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex min-w-[180px] flex-1 items-center gap-2">
              <ZoomOut size={14} className="shrink-0 text-muted-foreground" />
              <Slider
                min={1}
                max={maxZoom}
                step={0.05}
                value={[zoom]}
                onValueChange={(value) => setZoom(value[0] ?? 1)}
                className="flex-1"
                aria-label="Zoom"
              />
              <ZoomIn size={14} className="shrink-0 text-muted-foreground" />
              <span className="w-10 text-right font-mono text-muted-foreground">
                {Math.round(zoom * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={rotate}
                className="h-8 gap-1 px-2.5 text-xs"
                title="Rotate 90 degrees"
              >
                <RotateCw size={13} />
                Rotate
              </Button>

              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={reset}
                className="h-8 gap-1 px-2.5 text-xs text-muted-foreground hover:text-foreground"
                title="Reset position and zoom"
              >
                <RefreshCw size={13} />
                Reset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
