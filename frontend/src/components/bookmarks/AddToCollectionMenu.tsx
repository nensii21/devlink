import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { FolderPlus, Check } from "lucide-react";
import { useBookmarkCollections } from "@/hooks/useBookmarkCollections";
import type { BookmarkCollection } from "@/api";

export function AddToCollectionMenu({
  bookmarkId,
  onAddToCollection,
}: {
  bookmarkId: string;
  onAddToCollection: (collectionId: string) => void;
}) {
  const { data: collections = [] } = useBookmarkCollections();

  if (collections.length === 0) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          aria-label="Add to collection"
          onClick={(e) => e.stopPropagation()}
        >
          <FolderPlus size={14} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel className="text-[12px] text-muted-foreground">
          Add to collection
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {collections.map((col: BookmarkCollection) => (
          <DropdownMenuItem
            key={col.id}
            onClick={(e) => {
              e.stopPropagation();
              onAddToCollection(col.id);
            }}
          >
            <span className="flex-1 truncate text-[13px]">{col.name}</span>
            <span className="ml-2 text-[11px] text-muted-foreground">{col.bookmark_count}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function BookmarkCollectionIndicator({ bookmarkId }: { bookmarkId: string }) {
  const { data: bookmarkCollections = [] } = useBookmarkCollections();

  if (bookmarkCollections.length === 0) return null;

  return (
    <div className="flex items-center gap-1" aria-label="In collections">
      <Check size={12} className="text-primary" />
      <span className="text-[11px] text-muted-foreground">{bookmarkCollections.length}</span>
    </div>
  );
}
