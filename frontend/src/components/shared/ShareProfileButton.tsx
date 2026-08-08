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

export type ShareProfileButtonProps = {
  profileName: string;
  profileHandle: string;
  profileUrl?: string;
  profileBio?: string;
  className?: string;
};

type CopyKind = "link" | "text" | null;

export function ShareProfileButton({
  profileName,
  profileHandle,
  profileUrl,
  profileBio,
  className,
}: ShareProfileButtonProps) {
  const [hasNativeShare, setHasNativeShare] = useState(false);
  const [copiedKind, setCopiedKind] = useState<CopyKind>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setHasNativeShare(typeof navigator !== "undefined" && typeof navigator.share === "function");
  }, []);

  const canonicalUrl = useMemo(() => {
    if (profileUrl || typeof window === "undefined") return profileUrl ?? "";

    const url = new URL(window.location.href);
    url.search = "";
    url.hash = "";
    return url.toString();
  }, [profileUrl]);
  const shareText = useMemo(() => {
    const bio = profileBio?.trim();
    return [
      `Check out ${profileName}'s (@${profileHandle}) profile on DevLink`,
      bio && bio.length <= 240 ? bio : null,
      canonicalUrl,
    ]
      .filter(Boolean)
      .join("\n");
  }, [canonicalUrl, profileBio, profileName, profileHandle]);

  const showCopied = useCallback((kind: Exclude<CopyKind, null>) => {
    setCopiedKind(kind);
    window.setTimeout(() => setCopiedKind(null), 2000);
  }, []);

  const handleCopy = useCallback(
    async (kind: Exclude<CopyKind, null>) => {
      try {
        await copyText(kind === "link" ? canonicalUrl : shareText);
        showCopied(kind);
        toast.success(kind === "link" ? "Profile link copied" : "Profile text copied");
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
        title: `${profileName} on DevLink`,
        text: shareText,
        url: canonicalUrl,
      });
      toast.success("Profile shared");
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
      toast.error("Could not share this profile");
    }
  }, [canonicalUrl, profileName, shareText]);

  const button = (
    <Button
      type="button"
      className={className || "w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold"}
      aria-label="Share profile"
      onClick={hasNativeShare ? handleNativeShare : undefined}
    >
      {copiedKind ? (
        <Check size={16} aria-hidden="true" className="mr-2" />
      ) : (
        <Share2 size={16} aria-hidden="true" className="mr-2" />
      )}
      <span>{copiedKind ? "Copied" : "Share Profile"}</span>
    </Button>
  );

  if (hasNativeShare) return button;

  return (
    <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
      <DropdownMenuTrigger asChild>{button}</DropdownMenuTrigger>
      <DropdownMenuContent
        align="center"
        className="w-full min-w-[16rem]"
        aria-label="Share profile options"
      >
        <DropdownMenuItem onSelect={() => void handleCopy("link")}>
          {copiedKind === "link" ? (
            <Check size={14} className="text-success mr-2" aria-hidden="true" />
          ) : (
            <LinkIcon size={14} aria-hidden="true" className="mr-2" />
          )}
          <span>{copiedKind === "link" ? "Copied" : "Copy profile link"}</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void handleCopy("text")}>
          {copiedKind === "text" ? (
            <Check size={14} className="text-success mr-2" aria-hidden="true" />
          ) : (
            <Copy size={14} aria-hidden="true" className="mr-2" />
          )}
          <span>{copiedKind === "text" ? "Copied" : "Copy as text"}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
