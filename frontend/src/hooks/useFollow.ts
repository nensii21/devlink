import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  followUser,
  unfollowUser,
  getFollowStatus,
  toastError,
  type UUID,
  type FollowStatusResponse,
} from "@/lib/api";

export function useFollowStatus(userId: UUID | undefined) {
  return useQuery({
    queryKey: ["follow-status", userId],
    queryFn: () => getFollowStatus(userId!),
    enabled: !!userId,
  });
}

export function useFollow(userId: UUID) {
  const queryClient = useQueryClient();
  const queryKey = ["follow-status", userId];

  return useMutation({
    mutationFn: () => followUser(userId),

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey });

      const previous = queryClient.getQueryData<FollowStatusResponse>(queryKey);

      queryClient.setQueryData<FollowStatusResponse>(queryKey, (old) =>
        old
          ? {
              ...old,
              is_following: true,
              follower_count: old.follower_count + 1,
            }
          : { is_following: true, follower_count: 1, following_count: 0 },
      );

      return { previous };
    },

    onError: (err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      toastError(err, "Failed to follow");
    },

    onSuccess: (data) => {
      queryClient.setQueryData<FollowStatusResponse>(queryKey, {
        is_following: true,
        follower_count: data.follower_count,
        following_count: data.following_count,
      });
      toast.success("Followed successfully");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });
}

export function useUnfollow(userId: UUID) {
  const queryClient = useQueryClient();
  const queryKey = ["follow-status", userId];

  return useMutation({
    mutationFn: () => unfollowUser(userId),

    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey });

      const previous = queryClient.getQueryData<FollowStatusResponse>(queryKey);

      queryClient.setQueryData<FollowStatusResponse>(queryKey, (old) =>
        old
          ? {
              ...old,
              is_following: false,
              follower_count: Math.max(0, old.follower_count - 1),
            }
          : { is_following: false, follower_count: 0, following_count: 0 },
      );

      return { previous };
    },

    onError: (err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      toastError(err, "Failed to unfollow");
    },

    onSuccess: (data) => {
      queryClient.setQueryData<FollowStatusResponse>(queryKey, {
        is_following: false,
        follower_count: data.follower_count,
        following_count: data.following_count,
      });
      toast.success("Unfollowed successfully");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });
}
