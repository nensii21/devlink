import React from "react";
import { Button } from "../ui/button";
import { RotateCcw, Check } from "lucide-react";

interface CameraPreviewProps {
  imageFile: File;
  onRetake: () => void;
  onConfirm: (file: File) => void;
}

export const CameraPreview: React.FC<CameraPreviewProps> = ({ imageFile, onRetake, onConfirm }) => {
  const imageUrl = React.useMemo(() => URL.createObjectURL(imageFile), [imageFile]);

  // Clean up URL on unmount or when image changes
  React.useEffect(() => {
    return () => {
      URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  return (
    <div className="flex flex-col items-center w-full gap-4">
      <div className="relative w-full overflow-hidden rounded-lg bg-black flex justify-center items-center h-[300px] md:h-[400px]">
        <img src={imageUrl} alt="Captured" className="max-h-full max-w-full object-contain" />
      </div>

      <div className="flex w-full gap-4 justify-center">
        <Button variant="outline" onClick={onRetake} className="w-full sm:w-auto">
          <RotateCcw className="mr-2 h-4 w-4" />
          Retake
        </Button>
        <Button onClick={() => onConfirm(imageFile)} className="w-full sm:w-auto">
          <Check className="mr-2 h-4 w-4" />
          Use Photo
        </Button>
      </div>
    </div>
  );
};
