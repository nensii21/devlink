import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { bookmarksApi, type BookmarkResponse } from "@/api/modules/bookmarks";

const BOOKMARKS_KEY = ["user-bookmarks"] as const;

export interface BookmarkStatus {
  bookmarked: boolean;
  bookmarkId: string | null;
}

function deriveStatus(
  bookmarks: BookmarkResponse[] | undefined,
  projectId: string,
): BookmarkStatus {
  const match = bookmarks?.find((b) => b.project_id === projectId);
  return { bookmarked: !!match, bookmarkId: match?.id ?? null };
}

export function useBookmarkStatus(projectId: string) {
  const { data: bookmarks, ...rest } = useQuery({
    queryKey: BOOKMARKS_KEY,
    queryFn: () => bookmarksApi.list(),
  });

  return {
    ...rest,
    data: deriveStatus(bookmarks, projectId),
  };
}

export function useToggleBookmark(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const bookmarks = queryClient.getQueryData<BookmarkResponse[]>(BOOKMARKS_KEY);
      const status = deriveStatus(bookmarks, projectId);

      if (status.bookmarked && status.bookmarkId) {
        await bookmarksApi.remove(status.bookmarkId);
        return false;
      }
      await bookmarksApi.add(projectId);
      return true;
    },

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: BOOKMARKS_KEY });

      const previous = queryClient.getQueryData<BookmarkResponse[]>(BOOKMARKS_KEY);
      const status = deriveStatus(previous, projectId);

      if (status.bookmarked && status.bookmarkId) {
        queryClient.setQueryData<BookmarkResponse[]>(BOOKMARKS_KEY, (old) =>
          old?.filter((b) => b.project_id !== projectId),
        );
      } else {
        const optimistic: BookmarkResponse = {
          id: `optimistic-${projectId}`,
          user_id: "",
          project_id: projectId,
          created_at: new Date().toISOString(),
        };
        queryClient.setQueryData<BookmarkResponse[]>(BOOKMARKS_KEY, (old) => [
          optimistic,
          ...(old ?? []),
        ]);
      }

      return { previous };
    },

    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(BOOKMARKS_KEY, context.previous);
      }
      toast.error("Failed to update bookmark");
    },

    onSuccess: (bookmarked) => {
      toast.success(bookmarked ? "Bookmarked" : "Removed bookmark");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: BOOKMARKS_KEY });
    },
  });
}
