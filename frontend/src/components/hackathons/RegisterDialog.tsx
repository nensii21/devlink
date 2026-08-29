import { useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { hackathonsService } from "@/services";
import { TypoCaption } from "@/components/shared/Typography";

interface Props {
  hackathonId: string;
  hackathonName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called only on successful registration — not on cancel */
  onRegistered: () => void;
}

export function RegisterDialog({
  hackathonId,
  hackathonName,
  open,
  onOpenChange,
  onRegistered,
}: Props) {
  const [motivation, setMotivation] = useState("");
  const [loading, setLoading] = useState(false);

  function handleClose() {
    setMotivation("");
    onOpenChange(false);
  }

  async function handleRegister() {
    setLoading(true);
    try {
      await hackathonsService.register(hackathonId, {
        motivation: motivation.trim() || undefined,
      });
      toast.success("You're registered! Welcome to the hackathon.");
      setMotivation("");
      onRegistered(); // closes dialog AND marks registered
    } catch {
      toast.error("Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Register for {hackathonName}</DialogTitle>
          <DialogDescription>
            You'll be able to form or join a team after registering.
          </DialogDescription>
        </DialogHeader>

        <div>
          <label
            htmlFor="motivation"
            className="mb-1.5 block text-[13px] font-medium text-foreground"
          >
            What are you hoping to build?{" "}
            <TypoCaption className="font-normal text-muted-foreground">(optional)</TypoCaption>
          </label>
          <textarea
            id="motivation"
            value={motivation}
            onChange={(e) => setMotivation(e.target.value)}
            rows={4}
            placeholder="Describe your idea or what you want to learn…"
            className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <DialogFooter>
          <button
            type="button"
            onClick={handleClose}
            disabled={loading}
            className="rounded-md border border-border px-4 py-2 text-[13px] font-medium text-foreground hover:bg-muted disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleRegister}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {loading && <Loader2 size={13} className="animate-spin" />}
            Register
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
