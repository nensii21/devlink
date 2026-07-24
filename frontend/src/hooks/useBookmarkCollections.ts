import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { collectionsService } from "@/services";

const COLLECTIONS_KEY = ["bookmark-collections"];

export function useBookmarkCollections() {
  return useQuery({
    queryKey: COLLECTIONS_KEY,
    queryFn: () => collectionsService.list(),
  });
}

export function useBookmarkCollection(id: string | null) {
  return useQuery({
    queryKey: [...COLLECTIONS_KEY, id],
    queryFn: () => collectionsService.get(id!),
    enabled: !!id,
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => collectionsService.create(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
      toast.success("Collection created");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to create collection");
    },
  });
}

export function useRenameCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => collectionsService.rename(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
      toast.success("Collection renamed");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to rename collection");
    },
  });
}

export function useDeleteCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => collectionsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
      toast.success("Collection deleted");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to delete collection");
    },
  });
}

export function useAddBookmarkToCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ collectionId, bookmarkId }: { collectionId: string; bookmarkId: string }) =>
      collectionsService.addBookmark(collectionId, bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
      toast.success("Added to collection");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to add to collection");
    },
  });
}

export function useRemoveBookmarkFromCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ collectionId, bookmarkId }: { collectionId: string; bookmarkId: string }) =>
      collectionsService.removeBookmark(collectionId, bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
      toast.success("Removed from collection");
    },
    onError: (err: Error) => {
      toast.error(err.message || "Failed to remove from collection");
    },
  });
}
