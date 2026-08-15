import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { subscriptionsApi } from "@/api/modules/subscriptions";
import { TypoHeading, TypoCaption } from "@/components/shared/Typography";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2, Loader2, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/auth-context";

export function SubscriptionSection() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: subInfo, isLoading } = useQuery({
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
          };
        }
        throw err;
      }
    },
  });

  const upgradeMutation = useMutation({
    mutationFn: () => subscriptionsApi.upgrade("pro"),
    onSuccess: (data) => {
      toast.success("Subscription upgraded to Pro! Welcome aboard.");
      queryClient.invalidateQueries({ queryKey: ["subscriptions", "me"] });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      // In a real app we'd redirect to data.checkout_url if it's Stripe,
      // but since we return success directly in dev we just show success.
    },
    onError: () => {
      toast.error("Failed to upgrade subscription");
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isPro = subInfo?.tier === "pro" && subInfo?.status === "active";

  return (
    <div className="space-y-6">
      <div>
        <TypoHeading as="h2">Billing & Subscription</TypoHeading>
        <TypoCaption as="p">Manage your subscription and billing details</TypoCaption>
      </div>

      <div className="rounded-lg border border-border p-5 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Current plan</p>
            <TypoCaption as="p">You are on the {isPro ? "Pro" : "Free"} plan</TypoCaption>
            {isPro && subInfo?.current_period_end && (
              <TypoCaption as="p" className="mt-1">
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
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-muted-foreground" />
              <span>Payment methods</span>
            </div>
            <Button variant="outline" size="sm">
              Manage Billing
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
