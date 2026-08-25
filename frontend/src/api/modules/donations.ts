import { api } from "../client";

export interface DonationCreate {
  recipient_id: string;
  amount: number;
  message?: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export const DonationsApi = {
  createCheckoutSession: async (data: DonationCreate): Promise<CheckoutSessionResponse> => {
    const response = await api.post<CheckoutSessionResponse>('/donations/checkout', data);
    return response.data;
  }
};
