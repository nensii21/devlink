import React, { useEffect } from "react";
import { Attachment, UploadState } from "./types";
import { X, RefreshCw, FileText, BarChart, Book, Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TypoCaption } from "@/components/shared/Typography";

interface AttachmentPreviewProps {
  attachment: Attachment;
  uploadState?: UploadState;
  onRemove: () => void;
  onRetry?: () => void;
}

export const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({
  attachment,
  uploadState,
  onRemove,
  onRetry,
}) => {
  useEffect(() => {
    return () => {
      if (
        (attachment.type === "image" || attachment.type === "video" || attachment.type === "gif") &&
        attachment.previewUrl
      ) {
        URL.revokeObjectURL(attachment.previewUrl);
      }
    };
  }, [attachment]);

  const renderContent = () => {
    switch (attachment.type) {
      case "image":
      case "gif":
        return (
          <img
            src={attachment.previewUrl}
            alt="Attachment"
            className="w-full max-h-[300px] object-contain bg-black/5 rounded-md"
          />
        );
      case "video":
        return (
          <video
            src={attachment.previewUrl}
            controls
            className="w-full max-h-[300px] object-contain bg-black/5 rounded-md"
          />
        );
      case "repository":
        return (
          <div className="flex items-center gap-3 p-4 border rounded-md bg-muted/30">
            <Book className="w-8 h-8 text-muted-foreground" />
            <div>
              <p className="font-medium text-sm">Attached Repository</p>
              <TypoCaption as="p">{attachment.id}</TypoCaption>
            </div>
          </div>
        );
      case "project":
        return (
          <div className="flex items-center gap-3 p-4 border rounded-md bg-muted/30">
            <Briefcase className="w-8 h-8 text-muted-foreground" />
            <div>
              <p className="font-medium text-sm">Attached Project</p>
              <TypoCaption as="p">{attachment.id}</TypoCaption>
            </div>
          </div>
        );
      case "poll":
        return (
          <div className="flex items-center gap-3 p-4 border rounded-md bg-muted/30">
            <BarChart className="w-8 h-8 text-muted-foreground" />
            <div>
              <p className="font-medium text-sm">Poll</p>
              <TypoCaption as="p">{attachment.data.question}</TypoCaption>
            </div>
          </div>
        );
      case "article":
        return (
          <div className="flex items-center gap-3 p-4 border rounded-md bg-muted/30">
            <FileText className="w-8 h-8 text-muted-foreground" />
            <div>
              <p className="font-medium text-sm">Article</p>
              <TypoCaption as="p">{attachment.data.title}</TypoCaption>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const getFileName = () => {
    if (attachment.type === "image" || attachment.type === "video" || attachment.type === "gif") {
      return attachment.file.name;
    }
    return "";
  };

  return (
    <div className="relative group border rounded-md p-2 mt-2 bg-background">
      <div className="absolute top-4 right-4 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="secondary"
          size="icon"
          className="h-8 w-8 rounded-full shadow-md"
          onClick={onRemove}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {renderContent()}

      {uploadState && uploadState.status !== "idle" && (
        <div className="mt-2 text-xs font-mono">
          <div className="flex items-center justify-between mb-1">
            <span className="truncate max-w-[200px]">{getFileName()}</span>
            <span>{uploadState.progress}%</span>
          </div>
          <div className="w-full bg-secondary h-2 rounded-full overflow-hidden flex">
            <div
              className={`h-full ${
                uploadState.status === "error" ? "bg-destructive" : "bg-primary"
              } transition-all duration-300 ease-in-out`}
              style={{ width: `${uploadState.progress}%` }}
            />
          </div>
          {uploadState.status === "error" && (
            <div className="mt-1 text-destructive flex items-center justify-between">
              <span>Upload failed</span>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="text-primary hover:underline flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Retry
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
