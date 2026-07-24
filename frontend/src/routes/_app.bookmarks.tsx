import { useState, useCallback } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, EmptyState, TagChip, Avatar } from "@/components/shared/primitives";
import { projects, flares } from "@/mocks/seed";
import { Bookmark, FolderOpen, Trash2, MapPin, Briefcase, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CollectionSidebar } from "@/components/bookmarks/CollectionSidebar";
import { CollectionDialog } from "@/components/bookmarks/CollectionDialog";
import { AddToCollectionMenu } from "@/components/bookmarks/AddToCollectionMenu";
import { useBookmarks } from "@/context/BookmarkContext";
import {
  useCreateCollection,
  useRenameCollection,
  useDeleteCollection,
  useAddBookmarkToCollection,
} from "@/hooks/useBookmarkCollections";
import type { BookmarkCollection } from "@/api";

export const Route = createFileRoute("/_app/bookmarks")({
  head: () => ({
    meta: [
      { title: "Bookmarks — DevLink" },
      {
        name: "description",
        content: "Projects, builders and flares you've saved for later.",
      },
    ],
  }),
  component: BookmarksPage,
});

function BookmarksPage() {
  const [activeCollectionId, setActiveCollectionId] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<BookmarkCollection | null>(null);

  const { bookmarkedDevs, toggleBookmark } = useBookmarks();

  const createCollection = useCreateCollection();
  const renameCollection = useRenameCollection();
  const deleteCollection = useDeleteCollection();
  const addBookmarkToCollection = useAddBookmarkToCollection();

  const handleCreateCollection = useCallback(
    (name: string) => {
      createCollection.mutate(name, {
        onSuccess: () => setCreateDialogOpen(false),
      });
    },
    [createCollection]
  );

  const handleRenameCollection = useCallback(
    (name: string) => {
      if (!renameTarget) return;
      renameCollection.mutate(
        { id: renameTarget.id, name },
        {
          onSuccess: () => setRenameTarget(null),
        }
      );
    },
    [renameTarget, renameCollection]
  );

  const handleDeleteCollection = useCallback(
    (col: BookmarkCollection) => {
      deleteCollection.mutate(col.id, {
        onSuccess: () => {
          if (activeCollectionId === col.id) {
            setActiveCollectionId(null);
          }
        },
      });
    },
    [deleteCollection, activeCollectionId]
  );

  const handleAddToCollection = useCallback(
    (bookmarkId: string) => (collectionId: string) => {
      addBookmarkToCollection.mutate({
        collectionId,
        bookmarkId,
      });
    },
    [addBookmarkToCollection]
  );

  const bookmarkedProjects = projects.slice(0, 3);

  return (
    <div className="flex gap-6">
      <aside className="hidden w-56 shrink-0 md:block">
        <div className="sticky top-6">
          <CollectionSidebar
            activeCollectionId={activeCollectionId}
            onSelectCollection={setActiveCollectionId}
            onCreateCollection={() => setCreateDialogOpen(true)}
            onRenameCollection={setRenameTarget}
            onDeleteCollection={handleDeleteCollection}
          />
        </div>
      </aside>

      <div className="min-w-0 flex-1 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[22px] font-bold tracking-tight text-foreground">
              Bookmarks
            </h1>
            <p className="text-[13px] text-muted-foreground">
              {activeCollectionId
                ? "Filtered by collection"
                : "Projects, developers, and flares you've saved."}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="md:hidden"
            onClick={() => setCreateDialogOpen(true)}
          >
            <FolderOpen size={14} className="mr-1.5" />
            New Collection
          </Button>
        </div>

        {/* SAVED DEVELOPERS / BUILDERS SECTION */}
        <section>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[12px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Users size={14} /> Saved Developers
            </p>
          </div>
          {bookmarkedDevs.length === 0 ? (
            <Card className="p-6 text-center border-dashed">
              <p className="text-[13px] text-muted-foreground">
                No developers bookmarked yet. Save builders from their profiles to see them here!
              </p>
            </Card>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {bookmarkedDevs.map((dev) => (
                <Card key={dev.id} className="p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2.5">
                        <Avatar
                          src={dev.avatar_url || ""}
                          alt={dev.name || "Developer"}
                          size={40}
                        />
                        <div>
                          <p className="text-[14px] font-semibold text-foreground">
                            {dev.name}
                          </p>
                          <p className="text-[12px] text-muted-foreground">{dev.role}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => toggleBookmark(dev)}
                        title="Remove bookmark"
                        className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>

                    <div className="space-y-1 mb-3 text-[11px] text-muted-foreground">
                      {dev.location && (
                        <div className="flex items-center gap-1.5">
                          <MapPin size={12} />
                          <span>{dev.location}</span>
                        </div>
                      )}
                      {dev.experience && (
                        <div className="flex items-center gap-1.5">
                          <Briefcase size={12} />
                          <span>{dev.experience}</span>
                        </div>
                      )}
                    </div>

                    {dev.skills && dev.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {dev.skills.map((s) => (
                          <TagChip key={s}>{s}</TagChip>
                        ))}
                      </div>
                    )}
                  </div>

                  <Link
                    to="/builders/$builderId"
                    params={{ builderId: dev.id || "" }}
                    className="mt-2 block w-full text-center text-[12px] font-medium py-1.5 rounded-md border border-border hover:bg-muted text-foreground transition-colors"
                  >
                    View Profile
                  </Link>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* PROJECTS SECTION */}
        <section>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
              Projects
            </p>
          </div>
          {bookmarkedProjects.length === 0 ? (
            <EmptyState
              title="No bookmarked projects"
              desc="Save projects you're interested in to see them here."
            />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {bookmarkedProjects.map((p) => (
                <div key={p.id} className="group relative">
                  <Link to="/projects/$projectId" params={{ projectId: p.id }}>
                    <Card interactive className="p-4">
                      <div className="flex items-start gap-3">
                        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xl">
                          {p.icon}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[14px] font-semibold text-foreground">
                            {p.name}
                          </p>
                          <p className="mt-0.5 text-[12px] text-muted-foreground line-clamp-2">
                            {p.description}
                          </p>
                        </div>
                        <Bookmark size={14} className="text-primary fill-primary" />
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1">
                        {p.stack.map((s) => (
                          <TagChip key={s}>{s}</TagChip>
                        ))}
                      </div>
                    </Card>
                  </Link>
                  <div className="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100">
                    <AddToCollectionMenu
                      bookmarkId={p.id}
                      onAddToCollection={handleAddToCollection(p.id)}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* FLARES SECTION */}
        <section>
          <p className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-muted-foreground">
            Flares
          </p>
          <div className="space-y-2">
            {flares.slice(0, 2).map((f) => (
              <Card key={f.id} className="p-4">
                <p className="text-[13px] font-semibold text-foreground">
                  {f.author.name}
                </p>
                <p className="mt-1 text-[13px] text-foreground">{f.content}</p>
              </Card>
            ))}
          </div>
        </section>
      </div>

      <CollectionDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        title="New Collection"
        description="Create a collection to organize your bookmarks."
        onSubmit={handleCreateCollection}
      />

      <CollectionDialog
        open={!!renameTarget}
        onOpenChange={(open) => {
          if (!open) setRenameTarget(null);
        }}
        initialName={renameTarget?.name}
        title="Rename Collection"
        description="Give your collection a new name."
        onSubmit={handleRenameCollection}
      />
    </div>
  );
}
