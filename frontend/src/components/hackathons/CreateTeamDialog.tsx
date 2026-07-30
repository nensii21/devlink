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

interface Props {
  hackathonId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called after team is successfully created */
  onCreated: () => void;
}

export function CreateTeamDialog({ hackathonId, open, onOpenChange, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [nameError, setNameError] = useState("");

  function handleClose() {
    setName("");
    setDescription("");
    setNameError("");
    onOpenChange(false);
  }

  async function handleCreate() {
    const trimmed = name.trim();
    if (!trimmed) {
      setNameError("Team name is required.");
      return;
    }
    if (trimmed.length < 2) {
      setNameError("Must be at least 2 characters.");
      return;
    }

    setNameError("");
    setLoading(true);
    try {
      await hackathonsService.createTeam(hackathonId, {
        name: trimmed,
        description: description.trim() || undefined,
      });
      toast.success(`Team "${trimmed}" created!`);
      setName("");
      setDescription("");
      onCreated();
    } catch {
      toast.error("Failed to create team. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create a team</DialogTitle>
          <DialogDescription>
            Name your team and optionally describe what you're building.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <label
              htmlFor="team-name"
              className="mb-1.5 block text-[13px] font-medium text-foreground"
            >
              Team name <span className="text-destructive">*</span>
            </label>
            <input
              id="team-name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setNameError("");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder="e.g. Neural Nexus"
              maxLength={100}
              className={`w-full rounded-md border bg-surface px-3 py-2 text-[13px] outline-none focus:ring-2 focus:ring-primary/20 ${
                nameError
                  ? "border-destructive focus:border-destructive"
                  : "border-border focus:border-primary"
              }`}
              autoFocus
            />
            {nameError && <p className="mt-1 text-[12px] text-destructive">{nameError}</p>}
          </div>

          <div>
            <label
              htmlFor="team-desc"
              className="mb-1.5 block text-[13px] font-medium text-foreground"
            >
              Description <span className="font-normal text-muted-foreground">(optional)</span>
            </label>
            <textarea
              id="team-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="What are you planning to build?"
              maxLength={500}
              className="w-full resize-none rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
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
            onClick={handleCreate}
            disabled={loading || !name.trim()}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {loading && <Loader2 size={13} className="animate-spin" />}
            Create team
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
