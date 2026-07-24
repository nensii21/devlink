import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { postsApi } from "@/api";
import type { Flare } from "@/mocks/seed";

const LIKED_KEY = ["liked-flares"] as const;

function getLikedMap(qc: ReturnType<typeof useQueryClient>): Record<string, boolean> {
  return qc.getQueryData<Record<string, boolean>>(LIKED_KEY) ?? {};
}

export function useLikedFlares() {
  return useQuery({
    queryKey: LIKED_KEY,
    queryFn: () => Promise.resolve({} as Record<string, boolean>),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

export function useToggleLike(flareId: string) {
  const queryClient = useQueryClient();
  const flareQueryKey = ["flares"] as const;

  return useMutation({
    mutationFn: async () => {
      const liked = getLikedMap(queryClient);
      const isLiked = liked[flareId] ?? false;
      if (isLiked) {
        return postsApi.unlike(flareId);
      }
      return postsApi.like(flareId);
    },

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: LIKED_KEY });
      await queryClient.cancelQueries({ queryKey: flareQueryKey });

      const previousLiked = queryClient.getQueryData<Record<string, boolean>>(LIKED_KEY);
      const previousFlares = queryClient.getQueryData<Flare[]>(flareQueryKey);

      const isLiked = previousLiked?.[flareId] ?? false;

      queryClient.setQueryData<Record<string, boolean>>(LIKED_KEY, (old) => ({
        ...old,
        [flareId]: !isLiked,
      }));

      queryClient.setQueryData<Flare[]>(flareQueryKey, (old) =>
        old?.map((f) => (f.id === flareId ? { ...f, likes: f.likes + (isLiked ? -1 : 1) } : f)),
      );

      return { previousLiked, previousFlares };
    },

    onError: (_err, _vars, context) => {
      if (context?.previousLiked) {
        queryClient.setQueryData(LIKED_KEY, context.previousLiked);
      }
      if (context?.previousFlares) {
        queryClient.setQueryData(flareQueryKey, context.previousFlares);
      }
      toast.error("Failed to update like");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: LIKED_KEY });
      queryClient.invalidateQueries({ queryKey: flareQueryKey });
    },
  });
}
