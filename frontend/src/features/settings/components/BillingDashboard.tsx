import React, { useState } from "react";
import { Download, CreditCard, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/shared/primitives";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { TypoHeading, TypoSection, TypoCaption } from "@/components/shared/Typography";

// --- MOCK DATA ---
const MOCK_PLAN = {
  name: "Pro Plan",
  status: "Active",
  billingInterval: "monthly",
  nextBillingDate: "September 10, 2026",
  price: "$19.00",
};

const MOCK_USAGE = {
  storage: {
    used: 750,
    total: 1000,
    unit: "MB",
  },
};

const MOCK_PAYMENT_METHOD = {
  type: "Visa",
  last4: "4242",
  expiry: "08/28",
};

const MOCK_HISTORY = [
  {
    id: "inv_1",
    date: "Aug 01, 2026",
    description: "Pro Plan - Monthly",
    amount: "$19.00",
    status: "Paid",
    invoiceNo: "INV-2026-08-001",
  },
  {
    id: "inv_2",
    date: "Jul 01, 2026",
    description: "Pro Plan - Monthly",
    amount: "$19.00",
    status: "Paid",
    invoiceNo: "INV-2026-07-001",
  },
  {
    id: "inv_3",
    date: "Jun 01, 2026",
    description: "Pro Plan - Monthly",
    amount: "$19.00",
    status: "Paid",
    invoiceNo: "INV-2026-06-001",
  },
];

export function BillingDashboard() {
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);

  const usagePercent = (MOCK_USAGE.storage.used / MOCK_USAGE.storage.total) * 100;

  const handleCancelSubscription = async () => {
    setIsCanceling(true);
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsCanceling(false);
    setIsCancelModalOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Overview & Payment Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Subscription Overview */}
        <Card className="p-5 flex flex-col justify-between">
          <div>
            <TypoSection>Subscription Overview</TypoSection>
            <div className="mt-4 flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-foreground">{MOCK_PLAN.name}</p>
                <TypoCaption as="p">
                  {MOCK_PLAN.price} / {MOCK_PLAN.billingInterval}
                </TypoCaption>
              </div>
              <span className="rounded-full bg-success/10 px-3 py-1 text-xs font-semibold text-success">
                {MOCK_PLAN.status}
              </span>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-border">
            <TypoCaption as="p">
              Renews on{" "}
              <span className="font-medium text-foreground">{MOCK_PLAN.nextBillingDate}</span>
            </TypoCaption>
          </div>
        </Card>

        {/* Payment Method */}
        <Card className="p-5 flex flex-col justify-between">
          <div>
            <TypoSection>Payment Method</TypoSection>
            <div className="mt-4 flex items-center gap-4">
              <div className="grid h-12 w-16 place-items-center rounded bg-surface border border-border">
                <CreditCard className="text-muted-foreground" size={24} />
              </div>
              <div>
                <p className="font-semibold text-foreground">
                  {MOCK_PAYMENT_METHOD.type} ending in {MOCK_PAYMENT_METHOD.last4}
                </p>
                <TypoCaption as="p">Expires {MOCK_PAYMENT_METHOD.expiry}</TypoCaption>
              </div>
            </div>
          </div>
          <div className="mt-6">
            <Button variant="outline" size="sm">
              Update payment method
            </Button>
          </div>
        </Card>
      </div>

      {/* Usage Section */}
      <Card className="p-5">
        <TypoSection>Usage</TypoSection>
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Storage</span>
            <TypoCaption>
              {MOCK_USAGE.storage.used} {MOCK_USAGE.storage.unit} / {MOCK_USAGE.storage.total}{" "}
              {MOCK_USAGE.storage.unit}
            </TypoCaption>
          </div>
          <Progress value={usagePercent} className="h-2" />
          <TypoCaption as="p">{usagePercent.toFixed(0)}% of your plan limit used</TypoCaption>
        </div>
      </Card>

      {/* Billing History & Invoices */}
      <Card className="p-0 overflow-hidden">
        <div className="p-5 border-b border-border">
          <TypoSection>Billing History</TypoSection>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface/50 text-muted-foreground">
              <tr>
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-5 py-3 font-medium">Description</th>
                <th className="px-5 py-3 font-medium">Amount</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium text-right">Invoice</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {MOCK_HISTORY.map((item) => (
                <tr key={item.id} className="transition-colors hover:bg-muted/50">
                  <td className="px-5 py-3 text-foreground whitespace-nowrap">{item.date}</td>
                  <td className="px-5 py-3 text-foreground whitespace-nowrap">
                    {item.description}
                  </td>
                  <td className="px-5 py-3 text-foreground whitespace-nowrap">{item.amount}</td>
                  <td className="px-5 py-3 whitespace-nowrap">
                    <span className="rounded-full bg-success/10 px-2 py-0.5 text-xs font-semibold text-success">
                      {item.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right whitespace-nowrap">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 gap-1.5 text-muted-foreground hover:text-foreground"
                    >
                      <Download size={14} />
                      <span className="sr-only sm:not-sr-only">Download</span>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Plan Management Actions */}
      <Card className="p-5">
        <TypoSection>Plan Management</TypoSection>
        <p className="mt-2 text-sm text-muted-foreground">
          Upgrade your plan for more storage and features, or cancel your current subscription.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button>Upgrade Plan</Button>
          <Button variant="destructive" onClick={() => setIsCancelModalOpen(true)}>
            Cancel Subscription
          </Button>
        </div>
      </Card>

      {/* Cancel Confirmation Dialog */}
      <Dialog open={isCancelModalOpen} onOpenChange={setIsCancelModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Cancel subscription?</DialogTitle>
            <DialogDescription>
              Your subscription will remain active until the end of the current billing period (
              {MOCK_PLAN.nextBillingDate}). After that, you will be downgraded to the free plan.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setIsCancelModalOpen(false)}
              disabled={isCanceling}
            >
              Keep subscription
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelSubscription}
              disabled={isCanceling}
              className="gap-2"
            >
              {isCanceling && <Loader2 size={14} className="animate-spin" />}
              {isCanceling ? "Canceling..." : "Cancel subscription"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
