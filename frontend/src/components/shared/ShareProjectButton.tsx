import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, Copy, Link as LinkIcon, Share2 } from "lucide-react";
import { toast } from "sonner";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { copyText } from "@/lib/clipboard";

export type ShareProjectButtonProps = {
  projectTitle: string;
  projectUrl?: string;
  projectDescription?: string;
};

type CopyKind = "link" | "text" | null;

export function ShareProjectButton({
  projectTitle,
  projectUrl,
  projectDescription,
}: ShareProjectButtonProps) {
  const [hasNativeShare, setHasNativeShare] = useState(false);
  const [copiedKind, setCopiedKind] = useState<CopyKind>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setHasNativeShare(typeof navigator !== "undefined" && typeof navigator.share === "function");
  }, []);

  const canonicalUrl = useMemo(() => {
    if (projectUrl || typeof window === "undefined") return projectUrl ?? "";

    const url = new URL(window.location.href);
    url.search = "";
    url.hash = "";
    return url.toString();
  }, [projectUrl]);
  const shareText = useMemo(() => {
    const description = projectDescription?.trim();
    return [
      `Check out this project: ${projectTitle}`,
      description && description.length <= 240 ? description : null,
      canonicalUrl,
    ]
      .filter(Boolean)
      .join("\n");
  }, [canonicalUrl, projectDescription, projectTitle]);

  const showCopied = useCallback((kind: Exclude<CopyKind, null>) => {
    setCopiedKind(kind);
    window.setTimeout(() => setCopiedKind(null), 2000);
  }, []);

  const handleCopy = useCallback(
    async (kind: Exclude<CopyKind, null>) => {
      try {
        await copyText(kind === "link" ? canonicalUrl : shareText);
        showCopied(kind);
        toast.success(kind === "link" ? "Project link copied" : "Project text copied");
      } catch {
        toast.error("Could not copy to the clipboard");
      }
    },
    [canonicalUrl, shareText, showCopied],
  );

  const handleNativeShare = useCallback(async () => {
    if (!navigator.share) return;

    try {
      await navigator.share({
        title: projectTitle,
        text: shareText,
        url: canonicalUrl,
      });
      toast.success("Project shared");
    } catch (error) {
      if (
        (error instanceof DOMException && error.name === "AbortError") ||
        (typeof error === "object" &&
          error !== null &&
          "name" in error &&
          error.name === "AbortError")
      ) {
        return;
      }
      toast.error("Could not share this project");
    }
  }, [canonicalUrl, projectTitle, shareText]);

  const button = (
    <Button
      type="button"
      variant="outline"
      size="sm"
      aria-label="Share project"
      onClick={hasNativeShare ? handleNativeShare : undefined}
    >
      {copiedKind ? (
        <Check size={14} aria-hidden="true" />
      ) : (
        <Share2 size={14} aria-hidden="true" />
      )}
      <span>{copiedKind ? "Copied" : "Share"}</span>
    </Button>
  );

  if (hasNativeShare) return button;

  return (
    <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
      <DropdownMenuTrigger asChild>{button}</DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-[min(16rem,calc(100vw-2rem))]"
        aria-label="Share project options"
      >
        <DropdownMenuItem onSelect={() => void handleCopy("link")}>
          {copiedKind === "link" ? (
            <Check size={14} className="text-success" aria-hidden="true" />
          ) : (
            <LinkIcon size={14} aria-hidden="true" />
          )}
          <span>{copiedKind === "link" ? "Copied" : "Copy project link"}</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void handleCopy("text")}>
          {copiedKind === "text" ? (
            <Check size={14} className="text-success" aria-hidden="true" />
          ) : (
            <Copy size={14} aria-hidden="true" />
          )}
          <span>{copiedKind === "text" ? "Copied" : "Copy as text"}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
