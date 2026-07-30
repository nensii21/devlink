import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
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
import type { Hackathon } from "@/services";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface F {
  name: string;
  description: string;
  theme: string;
  prize: string;
  starts_at: string;
  ends_at: string;
  min_team_size: string;
  max_team_size: string;
  website_url: string;
}

interface E {
  name?: string;
  description?: string;
  starts_at?: string;
  ends_at?: string;
  min_team_size?: string;
  max_team_size?: string;
}

const EMPTY: F = {
  name: "",
  description: "",
  theme: "",
  prize: "",
  starts_at: "",
  ends_at: "",
  min_team_size: "2",
  max_team_size: "4",
  website_url: "",
};

function fi(err?: string) {
  return `w-full rounded-md border bg-surface px-3 py-2 text-[13px] outline-none focus:ring-2 focus:ring-primary/20 ${err ? "border-destructive" : "border-border focus:border-primary"}`;
}

export function CreateHackathonDialog({ open, onOpenChange }: Props) {
  const navigate = useNavigate();
  const [form, setForm] = useState<F>(EMPTY);
  const [errors, setErrors] = useState<E>({});
  const [loading, setLoading] = useState(false);

  function set(k: keyof F, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
    setErrors((p) => ({ ...p, [k]: undefined }));
  }

  function validate(): boolean {
    const e: E = {};
    if (!form.name.trim()) e.name = "Name is required.";
    if (!form.description.trim()) e.description = "Description is required.";
    if (!form.starts_at) e.starts_at = "Start date is required.";
    if (!form.ends_at) e.ends_at = "End date is required.";
    if (form.starts_at && form.ends_at && form.ends_at <= form.starts_at)
      e.ends_at = "End must be after start.";
    const min = parseInt(form.min_team_size);
    const max = parseInt(form.max_team_size);
    if (!min || min < 1) e.min_team_size = "Must be at least 1.";
    if (!max || max < 1) e.max_team_size = "Must be at least 1.";
    if (min && max && max < min) e.max_team_size = "Max must be ≥ min.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleClose() {
    setForm(EMPTY);
    setErrors({});
    onOpenChange(false);
  }

  async function handleCreate() {
    if (!validate()) return;
    setLoading(true);
    try {
      const body: Partial<Hackathon> = {
        name: form.name.trim(),
        description: form.description.trim(),
        theme: form.theme.trim() || undefined,
        prize: form.prize.trim() || undefined,
        starts_at: new Date(form.starts_at).toISOString(),
        ends_at: new Date(form.ends_at).toISOString(),
        min_team_size: parseInt(form.min_team_size),
        max_team_size: parseInt(form.max_team_size),
        website_url: form.website_url.trim() || undefined,
        status: "registration_open",
        is_published: true,
      };
      const created = await hackathonsService.create(body);
      toast.success("Hackathon created!");
      handleClose();
      // Navigate to the new hackathon if we got an ID back
      if (created && (created as Hackathon).id) {
        navigate({
          to: "/hackathons/$hackathonId",
          params: { hackathonId: (created as Hackathon).id },
        });
      }
    } catch {
      toast.error("Failed to create hackathon. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create a hackathon</DialogTitle>
          <DialogDescription>Fill in the details to launch your event.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Name <span className="text-destructive">*</span>
            </label>
            <input
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. AI for Good 2025"
              maxLength={200}
              className={fi(errors.name)}
              autoFocus
            />
            {errors.name && <p className="mt-1 text-[12px] text-destructive">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Description <span className="text-destructive">*</span>
            </label>
            <textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              rows={3}
              placeholder="What is this hackathon about?"
              className={`${fi(errors.description)} resize-none`}
            />
            {errors.description && (
              <p className="mt-1 text-[12px] text-destructive">{errors.description}</p>
            )}
          </div>

          {/* Theme + Prize */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Theme <span className="font-normal text-muted-foreground">(optional)</span>
              </label>
              <input
                value={form.theme}
                onChange={(e) => set("theme", e.target.value)}
                placeholder="e.g. Social Impact"
                maxLength={200}
                className={fi()}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Prize <span className="font-normal text-muted-foreground">(optional)</span>
              </label>
              <input
                value={form.prize}
                onChange={(e) => set("prize", e.target.value)}
                placeholder="e.g. $10k"
                maxLength={100}
                className={fi()}
              />
            </div>
          </div>

          {/* Dates */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Starts <span className="text-destructive">*</span>
              </label>
              <input
                type="datetime-local"
                value={form.starts_at}
                onChange={(e) => set("starts_at", e.target.value)}
                className={fi(errors.starts_at)}
              />
              {errors.starts_at && (
                <p className="mt-1 text-[12px] text-destructive">{errors.starts_at}</p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Ends <span className="text-destructive">*</span>
              </label>
              <input
                type="datetime-local"
                value={form.ends_at}
                onChange={(e) => set("ends_at", e.target.value)}
                className={fi(errors.ends_at)}
              />
              {errors.ends_at && (
                <p className="mt-1 text-[12px] text-destructive">{errors.ends_at}</p>
              )}
            </div>
          </div>

          {/* Team sizes */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Min team size <span className="text-destructive">*</span>
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={form.min_team_size}
                onChange={(e) => set("min_team_size", e.target.value)}
                className={fi(errors.min_team_size)}
              />
              {errors.min_team_size && (
                <p className="mt-1 text-[12px] text-destructive">{errors.min_team_size}</p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Max team size <span className="text-destructive">*</span>
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={form.max_team_size}
                onChange={(e) => set("max_team_size", e.target.value)}
                className={fi(errors.max_team_size)}
              />
              {errors.max_team_size && (
                <p className="mt-1 text-[12px] text-destructive">{errors.max_team_size}</p>
              )}
            </div>
          </div>

          {/* Website */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Website URL <span className="font-normal text-muted-foreground">(optional)</span>
            </label>
            <input
              value={form.website_url}
              onChange={(e) => set("website_url", e.target.value)}
              placeholder="https://…"
              className={fi()}
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
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {loading && <Loader2 size={13} className="animate-spin" />}
            Create hackathon
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
