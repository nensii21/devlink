import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { toast } from "sonner";
import { type PostEngagement } from "@/api";
import { flaresService } from "@/services";
import type { Flare } from "@/mocks/seed";

/**
 * Liked-state for the current viewer.
 *
 * This used to be a react-query entry whose `queryFn` was
 * `() => Promise.resolve({})`. Nothing ever populated it from the server, so
 * after a reload every post read as un-liked, the heart rendered empty
 * regardless of what the viewer had done, and clicking it sent another
 * `POST /like` — which the old backend happily counted a second time.
 *
 * The server now returns `liked_by_me` on every post, so the map is derived
 * from the feed rather than guessed. Deriving it means there is one source of
 * truth: if the feed says a post is liked, the heart is filled, and the two
 * cannot drift apart across a reload.
 */
const FLARES_KEY = ["flares"] as const;

export type LikedMap = Record<string, boolean>;

function likedMapFromFlares(flares: Flare[] | undefined): LikedMap {
  const map: LikedMap = {};
  for (const flare of flares ?? []) {
    map[flare.id] = flare.liked_by_me ?? false;
  }
  return map;
}

/**
 * The viewer's liked posts, derived from the feed.
 *
 * Same `queryKey` *and* same `queryFn` as the feed query in
 * `routes/_app.flares.tsx`, so react-query dedupes the two into one request
 * rather than racing two fetchers over one cache entry. `select` narrows the
 * shared result to the map this hook's callers want.
 */
export function useLikedFlares() {
  return useQuery({
    queryKey: FLARES_KEY,
    queryFn: flaresService.list,
    select: likedMapFromFlares,
    staleTime: 30_000,
  });
}

export function useToggleLike(flareId: string) {
  const queryClient = useQueryClient();

  const isLikedNow = () => {
    const flares = queryClient.getQueryData<Flare[]>(FLARES_KEY);
    return flares?.find((f) => f.id === flareId)?.liked_by_me ?? false;
  };

  /**
   * The liked state as it was *before* this mutation started.
   *
   * `onMutate` runs before `mutationFn` and has already written the
   * optimistic flip into the cache by the time `mutationFn` is called, so
   * `mutationFn` cannot re-derive which request to send — it would read its
   * own optimistic update back and send the opposite one. The decision is
   * made once, in `onMutate`, and recorded here.
   */
  const wasLikedRef = useRef(false);

  return useMutation({
    mutationFn: async (): Promise<PostEngagement> => {
      return wasLikedRef.current
        ? flaresService.unlike(flareId)
        : flaresService.like(flareId);
    },

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: FLARES_KEY });

      const previousFlares = queryClient.getQueryData<Flare[]>(FLARES_KEY);
      const wasLiked = isLikedNow();
      wasLikedRef.current = wasLiked;

      queryClient.setQueryData<Flare[]>(FLARES_KEY, (old) =>
        old?.map((f) =>
          f.id === flareId
            ? {
                ...f,
                liked_by_me: !wasLiked,
                // Never below zero: the optimistic guess can be wrong if the
                // server disagrees about the previous state, and a negative
                // count on screen is worse than a stale one.
                likes: Math.max(0, f.likes + (wasLiked ? -1 : 1)),
              }
            : f,
        ),
      );

      return { previousFlares };
    },

    /**
     * The server is authoritative about both the count and whether the viewer
     * has liked the post, and it returns both. Writing them back means a
     * second click on a post that was already liked settles on the truth
     * instead of on our optimistic guess.
     */
    onSuccess: (engagement) => {
      queryClient.setQueryData<Flare[]>(FLARES_KEY, (old) =>
        old?.map((f) =>
          f.id === flareId
            ? { ...f, likes: engagement.likes, liked_by_me: engagement.liked_by_me }
            : f,
        ),
      );
    },

    onError: (_err, _vars, context) => {
      if (context?.previousFlares) {
        queryClient.setQueryData(FLARES_KEY, context.previousFlares);
      }
      toast.error("Failed to update like");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: FLARES_KEY });
    },
  });
}
