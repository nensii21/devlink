import { useMemo } from "react";
import { Folder, Star, Plus, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/shared/primitives";
import { useBookmarkCollections } from "@/hooks/useBookmarkCollections";
import type { BookmarkCollection } from "@/api";

export function CollectionSidebar({
  activeCollectionId,
  onSelectCollection,
  onCreateCollection,
  onRenameCollection,
  onDeleteCollection,
}: {
  activeCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onCreateCollection: () => void;
  onRenameCollection: (collection: BookmarkCollection) => void;
  onDeleteCollection: (collection: BookmarkCollection) => void;
}) {
  const { data: collections = [], isLoading } = useBookmarkCollections();

  const totalBookmarks = useMemo(
    () => collections.reduce((sum, c) => sum + c.bookmark_count, 0),
    [collections],
  );

  return (
    <nav aria-label="Bookmark collections" className="space-y-1">
      <div className="flex items-center justify-between px-1 pb-2">
        <h3 className="text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
          Collections
        </h3>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={onCreateCollection}
          aria-label="Create new collection"
        >
          <Plus size={14} />
        </Button>
      </div>

      <CollectionItem
        label="All Bookmarks"
        count={totalBookmarks}
        icon={<Star size={14} />}
        active={activeCollectionId === null}
        onClick={() => onSelectCollection(null)}
      />

      {isLoading ? (
        <div className="space-y-2 px-1 pt-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-3/4" />
        </div>
      ) : (
        collections
          .filter((c) => !c.is_default)
          .map((col) => (
            <CollectionItem
              key={col.id}
              label={col.name}
              count={col.bookmark_count}
              icon={<Folder size={14} />}
              active={activeCollectionId === col.id}
              onClick={() => onSelectCollection(col.id)}
              onRename={() => onRenameCollection(col)}
              onDelete={!col.is_default ? () => onDeleteCollection(col) : undefined}
            />
          ))
      )}

      {collections.filter((c) => !c.is_default).length === 0 && !isLoading && (
        <p className="px-1 py-2 text-[12px] text-muted-foreground">
          No collections yet. Create one to organize your bookmarks.
        </p>
      )}
    </nav>
  );
}

function CollectionItem({
  label,
  count,
  icon,
  active,
  onClick,
  onRename,
  onDelete,
}: {
  label: string;
  count: number;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
  onRename?: () => void;
  onDelete?: () => void;
}) {
  return (
    <div className="group relative">
      <button
        onClick={onClick}
        className={cn(
          "flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-[13px] font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary",
          active
            ? "bg-primary-soft font-semibold text-primary"
            : "text-foreground/80 hover:bg-sidebar-accent hover:text-foreground",
        )}
        aria-current={active ? "page" : undefined}
      >
        <span className={cn(active ? "text-primary" : "text-muted-foreground")}>{icon}</span>
        <span className="flex-1 truncate text-left">{label}</span>
        <span className={cn("text-[11px]", active ? "text-primary/70" : "text-muted-foreground")}>
          {count}
        </span>
        {onRename && onDelete && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <span
                role="button"
                tabIndex={0}
                className="invisible ml-1 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground group-hover:visible focus-visible:visible focus-visible:ring-2 focus-visible:ring-primary"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.stopPropagation();
                  }
                }}
                aria-label={`Options for ${label}`}
              >
                <MoreHorizontal size={14} />
              </span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onRename();
                }}
              >
                <Pencil size={14} className="mr-2" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <DropdownMenuItem
                    onSelect={(e) => e.preventDefault()}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 size={14} className="mr-2" />
                    Delete
                  </DropdownMenuItem>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete "{label}"?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will remove the collection but not the bookmarks themselves. This action
                      cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                      }}
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </button>
    </div>
  );
}
