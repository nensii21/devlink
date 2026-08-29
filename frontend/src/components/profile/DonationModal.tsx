import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { DonationsApi } from "@/api/modules/donations";
import { useMutation } from "@tanstack/react-query";
import { Heart } from "lucide-react";

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
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <Heart className="w-5 h-5 text-pink-500 fill-pink-500" />
            <DialogTitle>Support {recipientName}</DialogTitle>
          </div>
          <DialogDescription>
            Your contribution helps developers continue creating amazing open source projects and content.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-4 gap-2">
            {PRESET_AMOUNTS.map((preset) => (
              <Button
                key={preset}
                type="button"
                variant={amount === preset && !customAmount ? "default" : "outline"}
                onClick={() => {
                  setAmount(preset);
                  setCustomAmount("");
                }}
                className="py-2 font-semibold text-sm"
              >
                ${preset}
              </Button>
            ))}
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-muted-foreground">Custom Amount</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-muted-foreground text-sm">
                $
              </span>
              <Input
                type="number"
                min="1"
                placeholder="Other amount"
                value={customAmount}
                onChange={(e) => {
                  setCustomAmount(e.target.value);
                  setAmount(0);
                }}
                className="pl-7"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-muted-foreground">
              Leave a Message (Optional)
            </label>
            <Textarea
              rows={3}
              placeholder="Thank you for your hard work!"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            className="bg-pink-600 hover:bg-pink-700 text-white"
            onClick={handleDonate}
            disabled={donationMutation.isPending || (!amount && !customAmount)}
          >
            {donationMutation.isPending ? "Processing..." : "Proceed to Checkout"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
