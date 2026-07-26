import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  acceptApplication,
  applyToFlare,
  rejectApplication,
  withdrawApplication,
  type ApplicationResponse,
  type UUID,
} from "@/lib/api";

const PROJECT_APPS_KEY = (projectId: UUID) => ["projectApplications", projectId] as const;
const MY_APPS_KEY = ["myApplications"] as const;

function optimisticStatus(
  data: ApplicationResponse[] | undefined,
  appId: UUID,
  status: ApplicationResponse["status"],
): ApplicationResponse[] | undefined {
  if (!data) return data;
  return data.map((a) => (a.id === appId ? { ...a, status } : a));
}

export function useAcceptApplication(projectId: UUID) {
  const queryClient = useQueryClient();
  const key = PROJECT_APPS_KEY(projectId);

  return useMutation({
    mutationFn: (appId: UUID) => acceptApplication(appId),

    onMutate: async (appId) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<ApplicationResponse[]>(key);
      queryClient.setQueryData<ApplicationResponse[]>(key, (old) =>
        optimisticStatus(old, appId, "accepted"),
      );
      return { previous };
    },

    onError: (_err, appId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(key, context.previous);
      }
      toast.error("Failed to accept application");
    },

    onSuccess: () => {
      toast.success("Application accepted");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: key });
    },
  });
}

export function useRejectApplication(projectId: UUID) {
  const queryClient = useQueryClient();
  const key = PROJECT_APPS_KEY(projectId);

  return useMutation({
    mutationFn: (appId: UUID) => rejectApplication(appId),

    onMutate: async (appId) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<ApplicationResponse[]>(key);
      queryClient.setQueryData<ApplicationResponse[]>(key, (old) =>
        optimisticStatus(old, appId, "rejected"),
      );
      return { previous };
    },

    onError: (_err, appId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(key, context.previous);
      }
      toast.error("Failed to reject application");
    },

    onSuccess: () => {
      toast.success("Application rejected");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: key });
    },
  });
}

export function useWithdrawApplication(projectId?: UUID) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (appId: UUID) => withdrawApplication(appId),

    onMutate: async (appId) => {
      const projectKey = projectId ? PROJECT_APPS_KEY(projectId) : null;
      const myKey = MY_APPS_KEY;

      if (projectKey) {
        await queryClient.cancelQueries({ queryKey: projectKey });
      }
      await queryClient.cancelQueries({ queryKey: myKey });

      const previousProject = projectKey
        ? queryClient.getQueryData<ApplicationResponse[]>(projectKey)
        : undefined;
      const previousMy = queryClient.getQueryData<ApplicationResponse[]>(myKey);

      if (projectKey) {
        queryClient.setQueryData<ApplicationResponse[]>(projectKey, (old) =>
          optimisticStatus(old, appId, "withdrawn"),
        );
      }
      queryClient.setQueryData<ApplicationResponse[]>(myKey, (old) =>
        optimisticStatus(old, appId, "withdrawn"),
      );

      return { previousProject, previousMy, projectKey };
    },

    onError: (_err, _appId, context) => {
      if (context?.previousProject && context?.projectKey) {
        queryClient.setQueryData(context.projectKey, context.previousProject);
      }
      if (context?.previousMy) {
        queryClient.setQueryData(MY_APPS_KEY, context.previousMy);
      }
      toast.error("Failed to withdraw application");
    },

    onSuccess: () => {
      toast.success("Application withdrawn");
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: MY_APPS_KEY });
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: PROJECT_APPS_KEY(projectId) });
      }
    },
  });
}

export function useApplyToFlare() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      flareId,
      projectId,
      message,
      portfolioUrl,
      githubUrl,
    }: {
      flareId: UUID;
      projectId: UUID;
      message?: string;
      portfolioUrl?: string;
      githubUrl?: string;
    }) =>
      applyToFlare(flareId, projectId, {
        message,
        portfolio_url: portfolioUrl,
        github_url: githubUrl,
      }),

    onSuccess: () => {
      toast.success("Application submitted");
      queryClient.invalidateQueries({ queryKey: MY_APPS_KEY });
    },

    onError: (err: Error) => {
      toast.error(err.message || "Failed to apply");
    },
  });
}
