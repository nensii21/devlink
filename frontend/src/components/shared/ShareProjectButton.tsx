import { useState, useCallback } from "react";
import { Share2, Check, Copy, Link as LinkIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ShareProjectButtonProps {
  projectId: string;
  projectName: string;
  projectDescription: string;
  projectIcon: string;
}

export function ShareProjectButton({
  projectId,
  projectName,
  projectDescription,
  projectIcon,
}: ShareProjectButtonProps) {
  const [copied, setCopied] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const projectUrl = `${window.location.origin}/projects/${projectId}`;
  const shareTitle = `${projectIcon} ${projectName} — DevLink`;
  const shareText = `Check out ${projectName} on DevLink! ${projectDescription}`;

  const handleCopyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(projectUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = projectUrl;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    }
  }, [projectUrl]);

  const handleNativeShare = useCallback(async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url: projectUrl,
        });
      } catch (err) {
        // User cancelled or share failed — ignore
        if ((err as DOMException).name !== "AbortError") {
          console.error("Share failed:", err);
        }
      }
    }
  }, [shareTitle, shareText, projectUrl]);

  const hasNativeShare = typeof navigator !== "undefined" && "share" in navigator;

  // If native share is available, render a single button
  if (hasNativeShare) {
    return (
      <button
        type="button"
        onClick={handleNativeShare}
        className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-muted"
        aria-label="Share project"
      >
        <Share2 size={14} />
        Share
      </button>
    );
  }

  // Otherwise render a dropdown with copy options
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setShowMenu((v) => !v)}
        className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-2 text-[12px] font-medium text-foreground transition-colors hover:bg-muted"
        aria-label="Share project"
        aria-expanded={showMenu}
      >
        <Share2 size={14} />
        Share
      </button>

      {showMenu && (
        <>
          {/* Backdrop to close menu */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
            aria-hidden="true"
          />
          <div
            className="absolute right-0 top-full mt-1 z-20 min-w-[180px] rounded-md border border-border bg-card shadow-soft py-1"
            role="menu"
          >
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                handleCopyLink();
                setShowMenu(false);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-[12px] font-medium text-foreground hover:bg-muted transition-colors"
            >
              {copied ? <Check size={14} className="text-success" /> : <LinkIcon size={14} />}
              {copied ? "Link copied!" : "Copy project link"}
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                navigator.clipboard.writeText(`${shareText}\n\n${projectUrl}`);
                setCopied(true);
                window.setTimeout(() => setCopied(false), 2000);
                setShowMenu(false);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-[12px] font-medium text-foreground hover:bg-muted transition-colors"
            >
              <Copy size={14} />
              Copy as text
            </button>
          </div>
        </>
      )}
    </div>
  );
}
