import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { subscriptionsApi } from "@/api/modules/subscriptions";
import { paymentsApi } from "@/api/modules/payments";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2, Loader2, CreditCard, Download, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/auth-context";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export function SubscriptionSection() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [mockCardToken, setMockCardToken] = useState("");

  const { data: subInfo, isLoading: isSubLoading } = useQuery({
    queryKey: ["subscriptions", "me"],
    queryFn: async () => {
      try {
        return await subscriptionsApi.getSubscription();
      } catch (err: any) {
        if (err?.response?.status === 404) {
          return {
            tier: "free",
            status: "none",
            current_period_end: null,
            cancel_at_period_end: false,
            payment_method_last4: undefined,
            payment_method_brand: undefined,
          };
        }
        throw err;
      }
    },
  });

  const { data: payments, isLoading: isPaymentsLoading } = useQuery({
    queryKey: ["payments", "history"],
    queryFn: paymentsApi.getHistory,
    enabled: !!subInfo && subInfo.tier === "pro",
  });

  const upgradeMutation = useMutation({
    mutationFn: () => subscriptionsApi.upgrade("pro"),
    onSuccess: () => {
      toast.success("Subscription upgraded to Pro! Welcome aboard.");
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "me"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
    onError: () => {
      toast.error("Failed to upgrade subscription");
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => subscriptionsApi.cancel(),
    onSuccess: () => {
      toast.success("Subscription canceled.");
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "me"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
    onError: () => {
      toast.error("Failed to cancel subscription");
    },
  });

  const updateMethodMutation = useMutation({
    mutationFn: (token: string) => paymentsApi.updateMethod(token),
    onSuccess: (data) => {
      toast.success(`Payment method updated to ${data.brand} ending in ${data.last4}`);
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "me"] });
      setIsUpdateModalOpen(false);
      setMockCardToken("");
    },
    onError: () => {
      toast.error("Failed to update payment method");
    },
  });

  const handleUpdateMethod = (e: React.FormEvent) => {
    e.preventDefault();
    updateMethodMutation.mutate(mockCardToken);
  };

  const handleCancel = () => {
    if (window.confirm("Are you sure you want to cancel your Pro subscription?")) {
      cancelMutation.mutate();
    }
  };

  const downloadInvoice = (invoiceUrl?: string) => {
    if (invoiceUrl) {
      window.open(invoiceUrl, "_blank");
    } else {
      toast.info("Mock Invoice downloaded.");
    }
  };

  if (isSubLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isPro = subInfo?.tier === "pro" && subInfo?.status === "active";

  return (
    <div className="space-y-8">
      <div>
        <TypoHeading as="h2">Billing & Subscription</TypoHeading>
        <TypoCaption as="p">Manage your subscription and billing details</TypoCaption>
      </div>

      {/* Subscription Card */}
      <div className="rounded-lg border border-border p-5 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Current plan</p>
            <TypoCaption as="p">You are on the {isPro ? "Pro" : "Free"} plan</TypoCaption>
            {isPro && subInfo?.current_period_end && (
              <TypoCaption as="p" className="mt-1 text-primary">
                Renews on {new Date(subInfo.current_period_end).toLocaleDateString()}
              </TypoCaption>
            )}
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${isPro ? "bg-primary-soft text-primary" : "bg-muted text-muted-foreground"}`}
          >
            {isPro ? "Pro" : "Free"}
          </span>
        </div>

        <Separator />

        {!isPro ? (
          <div className="space-y-4">
            <h3 className="text-base font-semibold">Upgrade to Pro</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  <span>Unlimited applications</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  <span>Advanced Analytics & Insights</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  <span>See who viewed your profile</span>
                </div>
              </div>
              <div className="flex flex-col items-start justify-center md:items-end">
                <div className="mb-2 text-2xl font-bold">
                  $10<span className="text-sm font-normal text-muted-foreground">/mo</span>
                </div>
                <Button
                  onClick={() => upgradeMutation.mutate()}
                  disabled={upgradeMutation.isPending}
                  className="w-full md:w-auto"
                >
                  {upgradeMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Upgrade Now
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-muted-foreground" />
                <span>
                  {subInfo.payment_method_brand
                    ? `${subInfo.payment_method_brand} ending in ${subInfo.payment_method_last4}`
                    : "No payment method attached"}
                </span>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setIsUpdateModalOpen(true)}>
                  Update Method
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleCancel}
                  disabled={cancelMutation.isPending}
                >
                  {cancelMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Cancel Plan
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Payment History Card */}
      {isPro && (
        <div className="rounded-lg border border-border p-5 space-y-4">
          <h3 className="text-base font-semibold">Payment History</h3>
          <Separator />

          {isPaymentsLoading ? (
            <div className="py-8 flex justify-center">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : payments && payments.length > 0 ? (
            <div className="space-y-3">
              {payments.map((payment) => (
                <div
                  key={payment.id}
                  className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      ${(payment.amount / 100).toFixed(2)} {payment.currency.toUpperCase()}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(payment.created_at).toLocaleDateString()} &middot; {payment.status}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => downloadInvoice(payment.invoice_url)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Invoice
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              No payment history available.
            </p>
          )}
        </div>
      )}

      {/* Update Payment Method Modal */}
      <Dialog open={isUpdateModalOpen} onOpenChange={setIsUpdateModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Update Payment Method</DialogTitle>
            <DialogDescription>Enter a new card token (mock: mastercard)</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateMethod} className="space-y-4 mt-2">
            <div>
              <input
                required
                type="text"
                placeholder="tok_mastercard"
                className="w-full rounded-md border border-border bg-background p-2 text-sm text-foreground focus:border-primary focus:outline-none"
                value={mockCardToken}
                onChange={(e) => setMockCardToken(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setIsUpdateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateMethodMutation.isPending}>
                {updateMethodMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Save
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
