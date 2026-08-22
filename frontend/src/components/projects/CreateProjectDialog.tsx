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
import { TechStackSuggest } from "./TechStackSuggest";
import { ProjectTemplateSelect } from "./ProjectTemplateSelect";
import { TypoCaption } from "@/components/shared/Typography";
import { AIDescriptionGenerator } from "./AIDescriptionGenerator";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({ open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [warnings, setWarnings] = useState<SimilarProjectWarning[]>([]);
  const [pendingData, setPendingData] = useState<CreateProjectFormData | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | undefined>();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateProjectFormData>({
    resolver: zodResolver(createProjectSchema),
  });

  const projectIdea = watch("description") ?? "";

  function applyTechStack(techs: string[]) {
    if (techs.length === 0) return;
    const existing = (watch("tech_stack") ?? "")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    const merged = Array.from(new Set([...existing, ...techs]));
    setValue("tech_stack", merged.join(", "), { shouldValidate: false });
  }

  function handleClose() {
    reset();
    setWarnings([]);
    setPendingData(null);
    setSelectedTemplateId(undefined);
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
      <DialogContent className="w-[calc(100%-1.5rem)] sm:max-w-lg p-4 sm:p-6 max-h-[90dvh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-base sm:text-lg">New Project</DialogTitle>
        </DialogHeader>

        {warnings.length > 0 ? (
          <div className="space-y-4 overflow-y-auto pr-1">
            <div className="flex items-start gap-2.5 rounded-md border border-warning/40 bg-warning/10 p-3">
              <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
              <div className="space-y-1">
                <p className="text-[13px] font-semibold text-foreground">
                  Similar projects already exist
                </p>
                <TypoCaption as="p">Review these before creating a duplicate.</TypoCaption>
              </div>
            </div>

            <ul className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {warnings.map((w) => (
                <li
                  key={w.id}
                  className="rounded-md border border-border bg-surface p-3 text-[12px]"
                >
                  <p className="font-semibold text-foreground">{w.title}</p>
                  <TypoCaption as="p">
                    Title match: {Math.round(w.title_similarity * 100)}% · Description match:{" "}
                    {Math.round(w.description_similarity * 100)}%
                  </TypoCaption>
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

            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-2 border-t border-border sm:border-0">
              <Button
                variant="outline"
                className="w-full sm:w-auto"
                onClick={() => {
                  setWarnings([]);
                  setPendingData(null);
                }}
              >
                Go back
              </Button>
              <Button onClick={proceedAnyway} disabled={submitting} className="w-full sm:w-auto">
                {submitting ? <Loader2 size={14} className="animate-spin" /> : "Create anyway"}
              </Button>
            </div>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-3.5 sm:space-y-4 overflow-y-auto pr-1"
          >
            <div className="pb-2 mb-2 border-b border-border/50">
              <ProjectTemplateSelect
                selectedTemplateId={selectedTemplateId}
                onTemplateIdChange={setSelectedTemplateId}
                onSelect={(fields) => {
                  if (fields.description)
                    setValue("description", fields.description, { shouldValidate: true });
                  if (fields.stage)
                    setValue("stage", fields.stage as any, { shouldValidate: true });
                  if (fields.max_team_size)
                    setValue("max_team_size", fields.max_team_size, { shouldValidate: true });
                  if (fields.tech_stack)
                    setValue("tech_stack", fields.tech_stack, { shouldValidate: true });
                }}
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Title</Label>
              <Input
                {...register("title")}
                placeholder="My awesome project"
                className="bg-surface text-sm sm:text-[13px]"
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
                className="bg-surface text-sm sm:text-[13px]"
              />
            </div>

            <AIDescriptionGenerator
              onGenerated={(desc) => setValue("description", desc, { shouldValidate: true })}
            />

            <div className="space-y-1.5">
              <Label className="text-[12px] text-muted-foreground">Description</Label>
              <Textarea
                {...register("description")}
                placeholder="What are you building?"
                rows={3}
                className="bg-surface text-sm sm:text-[13px] min-h-[80px]"
              />
              {errors.description && (
                <p className="text-[11px] text-destructive">{errors.description.message}</p>
              )}
            </div>

            <TechStackSuggest projectIdea={projectIdea} onSelect={applyTechStack} />

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Stage</Label>
                <select
                  {...register("stage")}
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm sm:text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
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
                  className="bg-surface text-sm sm:text-[13px]"
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
                className="bg-surface text-sm sm:text-[13px]"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Repository URL</Label>
                <Input
                  {...register("repository_url")}
                  placeholder="https://github.com/…"
                  className="bg-surface text-sm sm:text-[13px]"
                />
                {errors.repository_url && (
                  <p className="text-[11px] text-destructive">{errors.repository_url.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12px] text-muted-foreground">Demo URL</Label>
                <Input
                  {...register("demo_url")}
                  placeholder="https://…"
                  className="bg-surface text-sm sm:text-[13px]"
                />
                {errors.demo_url && (
                  <p className="text-[11px] text-destructive">{errors.demo_url.message}</p>
                )}
              </div>
            </div>

            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-2 border-t border-border sm:border-0">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="w-full sm:w-auto">
                {submitting ? <Loader2 size={14} className="animate-spin" /> : "Create project"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
