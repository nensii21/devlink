import { api } from "../client";

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  features: string[];
}

export interface SubscriptionInfo {
  tier: "free" | "pro";
  status: "active" | "canceled" | "past_due" | "none";
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export const subscriptionsApi = {
  getSubscription: () => api.get<SubscriptionInfo>("/api/subscriptions/me"),
  upgrade: (tier: "pro") =>
    api.post<{ client_secret: string | null; checkout_url: string | null }>(
      "/api/subscriptions/upgrade",
      { tier },
    ),
};
