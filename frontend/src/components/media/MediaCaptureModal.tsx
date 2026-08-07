import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog";
import { CameraCapture } from "./CameraCapture";
import { CameraPreview } from "./CameraPreview";
import { MediaFallback } from "./MediaFallback";
import { isCameraSupported } from "../../utils/media";

interface MediaCaptureModalProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => void;
  title?: string;
}

type ModalView = "initial" | "camera" | "preview";

export const MediaCaptureModal: React.FC<MediaCaptureModalProps> = ({
  open,
  onClose,
  onUpload,
  title = "Choose an image",
}) => {
  const [view, setView] = useState<ModalView>("initial");
  const [capturedFile, setCapturedFile] = useState<File | null>(null);

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      handleClose();
    }
  };

  const handleClose = () => {
    setView("initial");
    setCapturedFile(null);
    onClose();
  };

  const handleCapture = (file: File) => {
    setCapturedFile(file);
    setView("preview");
  };

  const handleRetake = () => {
    setCapturedFile(null);
    setView("camera");
  };

  const handleConfirm = (file: File) => {
    onUpload(file);
    handleClose();
  };

  const handleFileSelect = (file: File) => {
    // Treat direct file upload identically to a captured image,
    // we can either go to preview or straight to confirm.
    setCapturedFile(file);
    setView("preview");
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[500px] w-full p-6">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="sr-only">Capture or upload a new image.</DialogDescription>
        </DialogHeader>

        <div className="mt-4 flex flex-col items-center justify-center min-h-[300px]">
          {view === "initial" && (
            <div className="w-full flex flex-col gap-4">
              {isCameraSupported() ? (
                <div className="flex flex-col gap-4">
                  <button
                    onClick={() => setView("camera")}
                    className="w-full py-6 px-4 border-2 border-dashed rounded-lg hover:bg-muted transition-colors flex flex-col items-center justify-center gap-2"
                  >
                    <span className="text-2xl">📷</span>
                    <span className="font-semibold">Take Photo</span>
                  </button>
                  <div className="relative flex items-center py-2">
                    <div className="flex-grow border-t border-border"></div>
                    <span className="flex-shrink-0 mx-4 text-muted-foreground text-sm">or</span>
                    <div className="flex-grow border-t border-border"></div>
                  </div>
                  <MediaFallback message="" onFileSelect={handleFileSelect} />
                </div>
              ) : (
                <MediaFallback message="Camera unavailable" onFileSelect={handleFileSelect} />
              )}
            </div>
          )}

          {view === "camera" && (
            <CameraCapture onCapture={handleCapture} onCancel={() => setView("initial")} />
          )}

          {view === "preview" && capturedFile && (
            <CameraPreview
              imageFile={capturedFile}
              onRetake={handleRetake}
              onConfirm={handleConfirm}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
