import React, { useState, useEffect, useRef, useCallback } from "react";
import { Camera, RefreshCcw, X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onCancel: () => void;
}

export function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [facingMode, setFacingMode] = useState<"user" | "environment">("user");
  const [hasMultipleCameras, setHasMultipleCameras] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices.filter((device) => device.kind === "videoinput");
      setHasMultipleCameras(videoInputs.length > 1);
    } catch (err) {
      console.warn("Could not enumerate devices", err);
    }
  };

  const startStream = useCallback(async () => {
    setError(null);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err: unknown) {
      console.error("Camera access error:", err);
      if (err instanceof Error) {
        if (err.name === "NotAllowedError") {
          setError("Camera permission denied. Please allow camera access in your browser.");
        } else if (err.name === "NotFoundError") {
          setError("No camera found on your device.");
        } else {
          setError(`Camera error: ${err.message}`);
        }
      } else {
        setError("Camera unavailable. You can upload an image instead.");
      }
    }
  }, [facingMode]);

  useEffect(() => {
    checkDevices();
    startStream();

    return () => {
      // Cleanup media stream tracks on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [startStream]);

  const handleSwitchCamera = () => {
    setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
  };

  const handleCapture = () => {
    if (!videoRef.current) return;

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      setError("Failed to capture image.");
      return;
    }

    // Draw video frame to canvas
    // Mirror the image horizontally if using the front-facing camera
    if (facingMode === "user") {
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
    }

    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Failed to process captured image.");
          return;
        }

        const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });

        // Stop stream before triggering capture callback
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
        }

        onCapture(file);
      },
      "image/jpeg",
      0.9,
    );
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center bg-muted/20 rounded-xl border-2 border-dashed border-border min-h-[300px]">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-4">
          <AlertCircle size={24} />
        </div>
        <p className="font-medium text-foreground mb-1">Camera Unavailable</p>
        <p className="text-sm text-muted-foreground mb-4 max-w-sm">{error}</p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={startStream}>
            Try Again
          </Button>
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-xl bg-black min-h-[300px] relative border border-border">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-[400px] object-cover"
        style={{ transform: facingMode === "user" ? "scaleX(-1)" : "none" }}
      />

      {/* Overlay Controls */}
      <div className="absolute inset-0 flex flex-col justify-between p-4 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none">
        {/* Top bar */}
        <div className="flex justify-end pointer-events-auto">
          <Button
            variant="ghost"
            size="icon"
            onClick={onCancel}
            className="text-white hover:bg-white/20 rounded-full h-8 w-8"
            title="Cancel"
          >
            <X size={18} />
          </Button>
        </div>

        {/* Bottom bar */}
        <div className="flex items-center justify-center gap-6 pointer-events-auto pb-2">
          <div className="flex-1 flex justify-end">
            {hasMultipleCameras && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSwitchCamera}
                className="text-white hover:bg-white/20 rounded-full h-12 w-12"
                title="Switch Camera"
              >
                <RefreshCcw size={22} />
              </Button>
            )}
          </div>

          <button
            onClick={handleCapture}
            className="h-16 w-16 rounded-full border-4 border-white/80 bg-white/30 flex items-center justify-center hover:bg-white/50 transition-colors focus:outline-none focus:ring-4 focus:ring-primary/50"
            title="Take Photo"
          >
            <div className="h-12 w-12 rounded-full bg-white flex items-center justify-center text-black">
              <Camera size={24} />
            </div>
          </button>

          <div className="flex-1" />
        </div>
      </div>
    </div>
  );
}
