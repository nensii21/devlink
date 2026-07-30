import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToggleBookmark, useBookmarkStatus } from "@/hooks/useBookmark";
import type { BookmarkTargetType } from "@/api/modules/bookmarks";
import { cn } from "@/lib/utils";

export function BookmarkToggleButton({
  targetType = "project",
  targetId,
  projectId,
  className,
}: {
  targetType?: BookmarkTargetType;
  targetId?: string;
  projectId?: string;
  className?: string;
}) {
  const actualTargetType: BookmarkTargetType = targetType ?? "project";
  const actualTargetId = targetId ?? projectId ?? "";
  const { data: status, isLoading } = useBookmarkStatus(actualTargetType, actualTargetId);
  const toggleBookmark = useToggleBookmark(actualTargetType, actualTargetId);
  const resolvedTargetType = targetType ?? "project";
  const resolvedTargetId = targetId ?? projectId ?? "";

  const { data: status, isLoading } = useBookmarkStatus(resolvedTargetType, resolvedTargetId);
  const toggleBookmark = useToggleBookmark(resolvedTargetType, resolvedTargetId);

  if (isLoading) {
    return (
      <Button variant="outline" size="sm" disabled className={cn("min-w-[100px]", className)}>
        <Loader2 size={14} className="animate-spin" />
      </Button>
    );
  }

  return (
    <Button
      variant={status.bookmarked ? "secondary" : "outline"}
      size="sm"
      onClick={() => toggleBookmark.mutate()}
      disabled={toggleBookmark.isPending}
      className={cn("min-w-[100px] transition-all", className)}
      aria-label={status.bookmarked ? "Remove bookmark" : "Add bookmark"}
      aria-pressed={status.bookmarked}
    >
      {toggleBookmark.isPending ? (
        <Loader2 size={14} className="animate-spin" />
      ) : status.bookmarked ? (
        <>
          <BookmarkCheck size={14} />
          Saved
        </>
      ) : (
        <>
          <Bookmark size={14} />
          Save
        </>
      )}
    </Button>
  );
}
