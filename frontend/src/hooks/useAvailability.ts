import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { availabilityApi } from "../api/modules/availability";
import { AvailabilityUpdate } from "../types/availability";
import { toast } from "sonner";

export const useMyAvailability = () => {
  return useQuery({
    queryKey: ["availability", "me"],
    queryFn: () => availabilityApi.getMyAvailability(),
  });
};

export const useUpdateAvailability = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AvailabilityUpdate) => availabilityApi.updateMyAvailability(data),
    onSuccess: (data) => {
      queryClient.setQueryData(["availability", "me"], data);
      toast.success("Availability settings updated successfully");
    },
    onError: () => {
      toast.error("Failed to update availability settings");
    },
  });
};

export const useUserAvailability = (username: string) => {
  return useQuery({
    queryKey: ["availability", username],
    queryFn: () => availabilityApi.getUserAvailability(username),
    enabled: !!username,
  });
};
