import { api } from "../client";

export interface PaymentHistoryItem {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  status: string;
  invoice_url?: string;
  created_at: string;
}

export const paymentsApi = {
  getHistory: () => api.get<PaymentHistoryItem[]>("/api/payments/history"),
  updateMethod: (token: string) =>
    api.post<{ message: string; brand: string; last4: string }>("/api/payments/update-method", {
      token,
    }),
};
