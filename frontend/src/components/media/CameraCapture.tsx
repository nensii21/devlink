import React, { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { Camera, SwitchCamera, X } from "lucide-react";
import { useCamera } from "../../hooks/useCamera";
import { MediaFallback } from "./MediaFallback";
import { dataUrlToFile } from "../../utils/media";

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onCancel: () => void;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onCancel }) => {
  const { cameraState, videoRef, errorMsg, startCamera, stopCamera, switchCamera } = useCamera();

  const [hasMultipleCameras, setHasMultipleCameras] = useState(false);

  useEffect(() => {
    startCamera();

    // Check if multiple cameras are available to show/hide the switch button
    navigator.mediaDevices
      .enumerateDevices()
      .then((devices) => {
        const videoInputs = devices.filter((device) => device.kind === "videoinput");
        setHasMultipleCameras(videoInputs.length > 1);
      })
      .catch(console.error);

    return () => stopCamera();
  }, [startCamera, stopCamera]);

  const handleCaptureClick = async () => {
    if (!videoRef.current) return;
    const video = videoRef.current;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    if (context) {
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.9);

      try {
        const file = await dataUrlToFile(dataUrl, `capture-${Date.now()}.jpg`);
        onCapture(file);
      } catch (err) {
        console.error("Failed to capture image:", err);
      }
    }
  };

  if (
    cameraState === "unavailable" ||
    cameraState === "permission_denied" ||
    cameraState === "error"
  ) {
    let message = "Camera access unavailable";
    if (cameraState === "permission_denied") {
      message = "Camera permission denied";
    } else if (cameraState === "error" && errorMsg) {
      message = errorMsg;
    }

    return <MediaFallback message={message} onFileSelect={onCapture} />;
  }

  return (
    <div className="flex flex-col items-center w-full gap-4">
      <div className="relative w-full overflow-hidden rounded-lg bg-black flex justify-center items-center h-[300px] md:h-[400px]">
        <video
          ref={videoRef}
          className="max-h-full max-w-full object-cover transform scale-x-[-1]"
          autoPlay
          playsInline
          muted
        />

        {cameraState === "requesting_permission" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 text-white p-4 text-center">
            <p>Please allow camera access in your browser.</p>
          </div>
        )}
      </div>

      <div className="flex w-full gap-4 justify-center items-center">
        {hasMultipleCameras && (
          <Button variant="outline" size="icon" onClick={switchCamera} title="Switch Camera">
            <SwitchCamera className="h-5 w-5" />
          </Button>
        )}

        <Button
          size="lg"
          onClick={handleCaptureClick}
          disabled={cameraState !== "ready"}
          className="w-full sm:w-auto px-8"
        >
          <Camera className="mr-2 h-5 w-5" />
          Capture
        </Button>

        <Button variant="outline" size="icon" onClick={onCancel} title="Cancel">
          <X className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
};
