import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Heart } from "lucide-react";

import { DonationsApi } from "@/api/modules/donations";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface DonationModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipientId: string;
  recipientName: string;
}

const PRESET_AMOUNTS = [5, 10, 25, 50];

export default function DonationModal({
  isOpen,
  onClose,
  recipientId,
  recipientName,
}: DonationModalProps) {
  const [amount, setAmount] = useState<number>(5);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [message, setMessage] = useState<string>("");

  const donationMutation = useMutation({
    mutationFn: DonationsApi.createCheckoutSession,
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });

  const handleDonate = () => {
    const finalAmount = customAmount ? parseInt(customAmount, 10) : amount;
    if (isNaN(finalAmount) || finalAmount < 1) return;

    donationMutation.mutate({
      recipient_id: recipientId,
      amount: finalAmount * 100, // Convert to cents
      message,
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md rounded-2xl border border-border bg-card p-6 shadow-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-lg font-medium leading-6 text-foreground">
            <Heart className="h-6 w-6 text-pink-500" />
            Support {recipientName}
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Your contribution helps developers continue creating amazing open source projects and
            content.
          </DialogDescription>
        </DialogHeader>

        <div className="mt-2 space-y-4">
          <div className="grid grid-cols-4 gap-2">
            {PRESET_AMOUNTS.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => {
                  setAmount(preset);
                  setCustomAmount("");
                }}
                className={cn(
                  "rounded-lg py-2 text-sm font-semibold transition-colors",
                  amount === preset && !customAmount
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/70 hover:text-foreground",
                )}
              >
                ${preset}
              </button>
            ))}
          </div>

          <div>
            <Label htmlFor="donation-custom-amount" className="mb-1 block text-sm font-medium">
              Custom Amount
            </Label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <span className="text-sm text-muted-foreground">$</span>
              </div>
              <input
                id="donation-custom-amount"
                type="number"
                min="1"
                placeholder="Other amount"
                value={customAmount}
                onChange={(e) => {
                  setCustomAmount(e.target.value);
                  setAmount(0);
                }}
                className="block w-full rounded-md border border-border bg-surface py-2 pl-7 pr-3 text-sm text-foreground shadow-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/20"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="donation-message" className="mb-1 block text-sm font-medium">
              Leave a Message (Optional)
            </Label>
            <textarea
              id="donation-message"
              rows={3}
              placeholder="Thank you for your hard work!"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="block w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/20"
            />
          </div>
        </div>

        <DialogFooter className="mt-4 gap-3 sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleDonate}
            disabled={donationMutation.isPending || (!amount && !customAmount)}
            className="bg-pink-600 text-white hover:bg-pink-700"
          >
            {donationMutation.isPending ? "Processing..." : "Proceed to Checkout"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
