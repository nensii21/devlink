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
import type { HackathonTeam } from "@/services";
import { hackathonsService } from "@/services";

interface Props {
  hackathonId: string;
  teams: HackathonTeam[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmitted: () => void;
}

interface Errors {
  team_id?: string;
  title?: string;
  description?: string;
  repo_url?: string;
  demo_url?: string;
}

function isUrl(v: string) {
  try {
    new URL(v);
    return true;
  } catch {
    return false;
  }
}

export function SubmitProjectDialog({
  hackathonId,
  teams,
  open,
  onOpenChange,
  onSubmitted,
}: Props) {
  const [teamId, setTeamId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [demoUrl, setDemoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Errors>({});

  function clrErr(k: keyof Errors) {
    setErrors((p) => ({ ...p, [k]: undefined }));
  }

  function validate(): boolean {
    const e: Errors = {};
    if (!teamId) e.team_id = "Select your team.";
    if (!title.trim()) e.title = "Title is required.";
    else if (title.trim().length < 3) e.title = "At least 3 characters.";
    if (!description.trim()) e.description = "Description is required.";
    else if (description.trim().length < 20) e.description = "At least 20 characters.";
    if (repoUrl && !isUrl(repoUrl)) e.repo_url = "Enter a valid URL.";
    if (demoUrl && !isUrl(demoUrl)) e.demo_url = "Enter a valid URL.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleClose() {
    setTeamId("");
    setTitle("");
    setDescription("");
    setRepoUrl("");
    setDemoUrl("");
    setErrors({});
    onOpenChange(false);
  }

  async function handleSubmit() {
    if (!validate()) return;
    setLoading(true);
    try {
      await hackathonsService.createSubmission(hackathonId, {
        team_id: teamId,
        title: title.trim(),
        description: description.trim(),
        repo_url: repoUrl.trim() || undefined,
        demo_url: demoUrl.trim() || undefined,
      });
      toast.success("Project submitted! Good luck 🚀");
      setTeamId("");
      setTitle("");
      setDescription("");
      setRepoUrl("");
      setDemoUrl("");
      onSubmitted();
    } catch {
      toast.error("Submission failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const inp = (err?: string) =>
    `w-full rounded-md border bg-surface px-3 py-2 text-[13px] outline-none focus:ring-2 focus:ring-primary/20 ${
      err ? "border-destructive focus:border-destructive" : "border-border focus:border-primary"
    }`;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Submit your project</DialogTitle>
          <DialogDescription>
            You can update this at any time before the deadline.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Team */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Team <span className="text-destructive">*</span>
            </label>
            <select
              value={teamId}
              onChange={(e) => {
                setTeamId(e.target.value);
                clrErr("team_id");
              }}
              className={inp(errors.team_id)}
            >
              <option value="">Select your team…</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            {errors.team_id && (
              <p className="mt-1 text-[12px] text-destructive">{errors.team_id}</p>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Project title <span className="text-destructive">*</span>
            </label>
            <input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                clrErr("title");
              }}
              placeholder="e.g. EcoTracker AI"
              maxLength={200}
              className={inp(errors.title)}
            />
            {errors.title && <p className="mt-1 text-[12px] text-destructive">{errors.title}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-foreground">
              Description <span className="text-destructive">*</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                clrErr("description");
              }}
              rows={4}
              placeholder="What does it do, how was it built, what's the impact?"
              className={`${inp(errors.description)} resize-none`}
            />
            {errors.description && (
              <p className="mt-1 text-[12px] text-destructive">{errors.description}</p>
            )}
          </div>

          {/* URLs */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Repository URL <span className="font-normal text-muted-foreground">(optional)</span>
              </label>
              <input
                value={repoUrl}
                onChange={(e) => {
                  setRepoUrl(e.target.value);
                  clrErr("repo_url");
                }}
                placeholder="https://github.com/…"
                className={inp(errors.repo_url)}
              />
              {errors.repo_url && (
                <p className="mt-1 text-[12px] text-destructive">{errors.repo_url}</p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground">
                Demo URL <span className="font-normal text-muted-foreground">(optional)</span>
              </label>
              <input
                value={demoUrl}
                onChange={(e) => {
                  setDemoUrl(e.target.value);
                  clrErr("demo_url");
                }}
                placeholder="https://…"
                className={inp(errors.demo_url)}
              />
              {errors.demo_url && (
                <p className="mt-1 text-[12px] text-destructive">{errors.demo_url}</p>
              )}
            </div>
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
            onClick={handleSubmit}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {loading && <Loader2 size={13} className="animate-spin" />}
            Submit project
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
