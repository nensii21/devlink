import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  bookmarksApi,
  type BookmarkResponse,
  type BookmarkTargetType,
} from "@/api/modules/bookmarks";

const BOOKMARKS_KEY = ["user-bookmarks"] as const;

export interface BookmarkStatus {
  bookmarked: boolean;
  bookmarkId: string | null;
}

function deriveStatus(
  bookmarks: BookmarkResponse[] | undefined,
  targetType: BookmarkTargetType,
  targetId: string,
): BookmarkStatus {
  const match = bookmarks?.find((b) => b.target_type === targetType && b.target_id === targetId);
  return { bookmarked: !!match, bookmarkId: match?.id ?? null };
}

export function useBookmarkStatus(targetType: BookmarkTargetType, targetId: string) {
  const { data: bookmarks, ...rest } = useQuery({
    queryKey: BOOKMARKS_KEY,
    queryFn: () => bookmarksApi.list(),
  });

  return {
    ...rest,
    data: deriveStatus(bookmarks, targetType, targetId),
  };
}

export function useBookmarkCount(targetType: BookmarkTargetType, targetId: string) {
  return useQuery({
    queryKey: [...BOOKMARKS_KEY, "count", targetType, targetId],
    queryFn: () => bookmarksApi.count(targetType, targetId),
  });
}

export function useToggleBookmark(targetType: BookmarkTargetType, targetId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const bookmarks = queryClient.getQueryData<BookmarkResponse[]>(BOOKMARKS_KEY);
      const status = deriveStatus(bookmarks, targetType, targetId);

      if (status.bookmarked && status.bookmarkId) {
        await bookmarksApi.remove(status.bookmarkId);
        return false;
      }
      await bookmarksApi.add(targetType, targetId);
      return true;
    },

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: BOOKMARKS_KEY });

      const previous = queryClient.getQueryData<BookmarkResponse[]>(BOOKMARKS_KEY);
      const status = deriveStatus(previous, targetType, targetId);

      if (status.bookmarked && status.bookmarkId) {
        queryClient.setQueryData<BookmarkResponse[]>(BOOKMARKS_KEY, (old) =>
          old?.filter((b) => !(b.target_type === targetType && b.target_id === targetId)),
        );
      } else {
        const optimistic: BookmarkResponse = {
          id: `optimistic-${targetType}-${targetId}`,
          user_id: "",
          target_type: targetType,
          target_id: targetId,
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
