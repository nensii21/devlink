import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { usersApi } from "@/api/modules/users";
import { ws } from "@/api/ws";
import type { CollaborationStatus } from "@/features/collaboration/types";

const QUERY_KEY = ["collaboration-status", "me"];

export function useCollaborationStatus() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => usersApi.getCollaborationStatus(),
    staleTime: 30_000,
  });

  const setStatusMutation = useMutation({
    mutationFn: (status: CollaborationStatus) => usersApi.setCollaborationStatus(status),
    onMutate: (status) => {
      queryClient.setQueryData<{ user_id: string; status: string }>(QUERY_KEY, {
        user_id: "",
        status,
      });
      // Broadcast the change to other connected clients in real-time.
      ws.updateCollaborationStatus(status);
    },
  });

  // Keep the local state in sync with live broadcasts from other clients.
  useEffect(() => {
    return ws.on((event) => {
      if (event.type === "presence.collaboration_status_changed") {
        const payload = event as any;
        const userId =
          typeof payload.userId === "string"
            ? payload.userId
            : typeof payload.user_id === "string"
              ? payload.user_id
              : undefined;
        if (userId && typeof payload.status === "string") {
          queryClient.setQueryData<{ user_id: string; status: string }>(QUERY_KEY, (old) => {
            if (!old) return old;
            return old.user_id === userId ? { ...old, status: payload.status } : old;
          });
        }
      }
    });
  }, [queryClient]);

  return {
    status: query.data?.status as CollaborationStatus | undefined,
    isLoading: query.isLoading,
    setStatus: setStatusMutation.mutate,
    isSetting: setStatusMutation.isPending,
  };
}
