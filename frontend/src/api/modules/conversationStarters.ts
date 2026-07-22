import { api } from "../client";

export interface ConversationStarterResponse {
  suggestions: string[];
  target_user_id: string;
  target_user_name: string;
}

export const conversationStartersApi = {
  generate: (targetUserId: string) =>
    api.post<ConversationStarterResponse>("/api/conversation-starters", {
      target_user_id: targetUserId,
    }),
};
