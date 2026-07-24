import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, AlertTriangle } from "lucide-react";

import { projectsApi, type SimilarProjectWarning } from "@/api/modules/projects";
import { createProjectSchema, type CreateProjectFormData } from "@/lib/schemas/forms";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [warnings, setWarnings] = useState<SimilarProjectWarning[]>([]);
  const [pendingData, setPendingData] = useState<CreateProjectFormData | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateProjectFormData>({
    resolver: zodResolver(createProjectSchema),
  });

  function handleClose() {
    reset();
    setWarnings([]);
    setPendingData(null);
    onOpenChange(false);
  }

  async function onSubmit(data: CreateProjectFormData) {
    if (submitting) return;
    setSubmitting(true);
    try {
      const similar = await projectsApi.checkSimilarity({
        title: data.title,
        description: data.description,
      });

      if (similar.length > 0 && !pendingData) {
        setWarnings(similar);
        setPendingData(data);
        return;
      }

      await projectsApi.create(data as never);
      toast.success("Project created");
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      handleClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  async function proceedAnyway() {
    if (!pendingData) return;
    setSubmitting(true);
    try {
      await projectsApi.create(pendingData as never);
      toast.success("Project created");
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      handleClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>New Project</DialogTitle>
        </DialogHeader>

        {warnings.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3">
              <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
              <div className="space-y-1">
                <p className="text-[13px] font-semibold text-foreground">
                  Similar projects already exist
                </p>
                <p className="text-[12px] text-muted-foreground">
                  Review these before creating a duplicate.
                </p>
              </div>
            </div>

            <ul className="space-y-2">
              {warnings.map((w) => (
                <li
                  key={w.id}
                  className="rounded-md border border-border bg-surface p-3 text-[12px]"
                >
                  <p className="font-semibold text-foreground">{w.title}</p>
                  <p className="mt-0.5 text-muted-foreground">
                    Title match: {Math.round(w.title_similarity * 100)}% · Description match:{" "}
                    {Math.round(w.description_similarity * 100)}%
                  </p>
                  <a
                    href={`/projects/${w.slug}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-block text-primary hover:underline"
                  >
                    View project →
                  </a>
                </li>
              ))}
            </ul>

            <div className="flex justify-end gap-2 pt-1">
              <Button
                variant="outline"
                onClick={() => {
                  setWarnings([]);
                  setPendingData(null);
                }}
              >
                Go back
              </Button>
              <Button onClick={proceedAnyway} disabled={submitting}>
                {submitting ? <Loader2 size={14} className="animate-spin" /> : "Create anyway"}
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Title</Label>
              <Input
                {...register("title")}
                placeholder="My awesome project"
                className="bg-surface"
              />
              {errors.title && (
                <p className="text-[11px] text-destructive">{errors.title.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Tagline</Label>
              <Input
                {...register("tagline")}
                placeholder="One-liner (optional)"
                className="bg-surface"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Description</Label>
              <Textarea
                {...register("description")}
                placeholder="What are you building?"
                rows={4}
                className="bg-surface"
              />
              {errors.description && (
                <p className="text-[11px] text-destructive">{errors.description.message}</p>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Stage</Label>
                <select
                  {...register("stage")}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                >
                  <option value="idea">Idea</option>
                  <option value="in_development">In Development</option>
                  <option value="beta">Beta</option>
                  <option value="launched">Launched</option>
                </select>
                {errors.stage && (
                  <p className="text-[11px] text-destructive">{errors.stage.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Max team size</Label>
                <Input
                  {...register("max_team_size", { valueAsNumber: true })}
                  type="number"
                  min={1}
                  max={100}
                  placeholder="5"
                  className="bg-surface"
                />
                {errors.max_team_size && (
                  <p className="text-[11px] text-destructive">{errors.max_team_size.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Tech stack</Label>
              <Input
                {...register("tech_stack")}
                placeholder="React, FastAPI, PostgreSQL…"
                className="bg-surface"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Repository URL</Label>
                <Input
                  {...register("repository_url")}
                  placeholder="https://github.com/…"
                  className="bg-surface"
                />
                {errors.repository_url && (
                  <p className="text-[11px] text-destructive">{errors.repository_url.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Demo URL</Label>
                <Input {...register("demo_url")} placeholder="https://…" className="bg-surface" />
                {errors.demo_url && (
                  <p className="text-[11px] text-destructive">{errors.demo_url.message}</p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? <Loader2 size={14} className="animate-spin" /> : "Create project"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
