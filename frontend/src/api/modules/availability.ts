import { api } from "../client";
import { UserAvailability, AvailabilityUpdate } from "../../types/availability";

export const availabilityApi = {
  getMyAvailability: async (): Promise<UserAvailability> => {
    return api.get<UserAvailability>("/api/availability/me");
  },

  updateMyAvailability: async (updateData: AvailabilityUpdate): Promise<UserAvailability> => {
    return api.put<UserAvailability>("/api/availability/me", updateData);
  },

  getUserAvailability: async (username: string): Promise<UserAvailability> => {
    return api.get<UserAvailability>(`/api/availability/${username}`);
  },
};
