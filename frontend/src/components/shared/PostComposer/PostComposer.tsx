import React, { useState, useRef } from "react";
import { MarkdownEditor } from "@/components/shared/MarkdownEditor";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { Button } from "@/components/ui/button";
import { Image, Camera, Video, FileVideo, GitMerge, Briefcase, BarChart, FileText, Send } from "lucide-react";
import { Attachment, UploadState } from "./types";
import { AttachmentPreview } from "./AttachmentPreview";
// Assuming MediaCaptureModal is available at the root or relative path. 
// From #960, we put it in src/components/media/MediaCaptureModal
import { MediaCaptureModal } from "@/components/media/MediaCaptureModal";

interface PostComposerProps {
  onPost: (content: string, attachments: Attachment[]) => Promise<void>;
  placeholder?: string;
  initialContent?: string;
}

export const PostComposer: React.FC<PostComposerProps> = ({
  onPost,
  placeholder = "What's on your mind?",
  initialContent = "",
}) => {
  const [content, setContent] = useState(initialContent);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploadStates, setUploadStates] = useState<Record<number, UploadState>>({});
  const [submitting, setSubmitting] = useState(false);
  const [cameraModalOpen, setCameraModalOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentUploadType, setCurrentUploadType] = useState<"image" | "video" | "gif">("image");

  const handlePost = async () => {
    if (!content.trim() && attachments.length === 0) return;
    setSubmitting(true);
    try {
      await onPost(content, attachments);
      setContent("");
      setAttachments([]);
      setUploadStates({});
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const newAttachments: Attachment[] = files.map((file) => ({
      type: currentUploadType,
      file,
      previewUrl: URL.createObjectURL(file),
    }));

    const startIndex = attachments.length;
    setAttachments((prev) => [...prev, ...newAttachments]);

    // Simulate upload progress
    newAttachments.forEach((_, idx) => {
      const stateIndex = startIndex + idx;
      simulateUpload(stateIndex);
    });
    
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const simulateUpload = (index: number) => {
    setUploadStates((prev) => ({
      ...prev,
      [index]: { progress: 0, status: "uploading" },
    }));

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 30;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setUploadStates((prev) => ({
          ...prev,
          [index]: { progress: 100, status: "uploaded" },
        }));
      } else {
        setUploadStates((prev) => ({
          ...prev,
          [index]: { progress: Math.floor(progress), status: "uploading" },
        }));
      }
    }, 500);
  };

  const handleCameraUpload = (file: File) => {
    const newAttachment: Attachment = {
      type: "image",
      file,
      previewUrl: URL.createObjectURL(file),
    };
    
    const index = attachments.length;
    setAttachments((prev) => [...prev, newAttachment]);
    simulateUpload(index);
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
    // Clean up upload states map if necessary, though it's ok to leave orphaned
  };

  const triggerFileInput = (type: "image" | "video" | "gif") => {
    setCurrentUploadType(type);
    if (fileInputRef.current) {
      if (type === "video") fileInputRef.current.accept = "video/*";
      else if (type === "gif") fileInputRef.current.accept = "image/gif";
      else fileInputRef.current.accept = "image/*";
      
      fileInputRef.current.click();
    }
  };

  const addMockAttachment = (type: "repository" | "project" | "poll" | "article") => {
    const attachment: Attachment = 
      type === "repository" ? { type: "repository", id: "mock-repo-123" } :
      type === "project" ? { type: "project", id: "mock-project-456" } :
      type === "poll" ? { type: "poll", data: { question: "What is your favorite framework?", options: ["React", "Vue", "Svelte"] } } :
      { type: "article", data: { title: "How to build a post composer", content: "..." } };
      
    setAttachments((prev) => [...prev, attachment]);
  };

  const isUploading = Object.values(uploadStates).some(state => state.status === "uploading");
  const canPost = (content.trim().length > 0 || attachments.length > 0) && !isUploading;

  return (
    <div className="flex flex-col gap-3">
      <MarkdownEditor
        value={content}
        onChange={setContent}
        placeholder={placeholder}
        rows={4}
      />
      
      {attachments.length > 0 && (
        <div className="flex flex-col gap-2 mt-2">
          {attachments.map((attachment, index) => (
            <AttachmentPreview 
              key={index}
              attachment={attachment}
              uploadState={uploadStates[index]}
              onRemove={() => removeAttachment(index)}
              onRetry={() => simulateUpload(index)}
            />
          ))}
        </div>
      )}

      <div className="flex items-center justify-between mt-2 flex-wrap gap-2">
        <div className="flex items-center overflow-x-auto pb-1 gap-1 -mb-1 hide-scrollbar">
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFileSelect} 
            multiple 
          />
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => triggerFileInput("image")} title="Add Image">
            <Image size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => setCameraModalOpen(true)} title="Take Photo">
            <Camera size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => triggerFileInput("video")} title="Add Video">
            <Video size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => triggerFileInput("gif")} title="Add GIF">
            <FileVideo size={18} />
          </Button>
          <div className="w-px h-6 bg-border mx-1 shrink-0"></div>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => addMockAttachment("repository")} title="Attach Repository">
            <GitMerge size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => addMockAttachment("project")} title="Attach Project">
            <Briefcase size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => addMockAttachment("poll")} title="Create Poll">
            <BarChart size={18} />
          </Button>
          <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground hover:text-foreground" onClick={() => addMockAttachment("article")} title="Write Article">
            <FileText size={18} />
          </Button>
        </div>

        <LoadingButton
          disabled={!canPost}
          loading={submitting}
          loadingText="Posting..."
          onClick={handlePost}
          size="sm"
          className="inline-flex items-center gap-1.5 rounded-full px-4"
        >
          <Send size={14} /> Post
        </LoadingButton>
      </div>

      <MediaCaptureModal 
        open={cameraModalOpen}
        onClose={() => setCameraModalOpen(false)}
        onUpload={handleCameraUpload}
        title="Take a photo for your post"
      />
    </div>
  );
};
