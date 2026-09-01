import { api } from "../client";
import type { User } from "@/lib/api";

export interface UserBlockResponse {
  id: string;
  blocker_id: string;
  blocked_id: string;
  created_at: string;
}

export interface BlockStatusResponse {
  is_blocked_by_me: boolean;
  is_blocking_me: boolean;
  has_block_relationship: boolean;
}

export const blocksApi = {
  blockUser: async (userId: string): Promise<UserBlockResponse> => {
    return api.post<UserBlockResponse>(`/api/blocks/${userId}`);
  },

  unblockUser: async (userId: string): Promise<void> => {
    return api.delete(`/api/blocks/${userId}`);
  },

  getBlockedUsers: async (): Promise<User[]> => {
    return api.get<User[]>("/api/blocks/");
  },

  getBlockStatus: async (userId: string): Promise<BlockStatusResponse> => {
    return api.get<BlockStatusResponse>(`/api/blocks/${userId}/status`);
  },
};
