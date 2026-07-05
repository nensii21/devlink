import { Card, TagChip } from "@/components/shared/primitives";
import { Cpu } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";

export interface TechStackCardProps {
  skills?: ProfileSkill[];
  techStack?: string[];
  editable?: boolean;
  formValues?: string[];
  error?: string;
  onTechStackChange?: (value: string) => void;
}

export function TechStackCard({ skills = [], techStack, editable = false, formValues = [], error, onTechStackChange }: TechStackCardProps) {
  const resolvedStack = (techStack?.filter(Boolean) ?? []).length
    ? techStack?.filter(Boolean) ?? []
    : skills.filter((skill) => Boolean(skill.category)).map((skill) => skill.name);

  const fallbackStack = resolvedStack.length === 0 ? skills.map((skill) => skill.name) : [];
  const stackItems = resolvedStack.length > 0 ? resolvedStack : fallbackStack;

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <Cpu size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Tech stack</h2>
            <p className="text-xs text-muted-foreground">List the tools you work with</p>
          </div>
        </div>

        <label className="mt-4 block text-sm">
          <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Technologies</span>
          <textarea
            value={formValues.join(", ")}
            onChange={(event) => onTechStackChange?.(event.target.value)}
            rows={4}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
            placeholder="React, Next.js, Tailwind CSS"
          />
          {error ? <p className="mt-1 text-xs text-red-500">{error}</p> : null}
        </label>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <Cpu size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Tech stack</h2>
          <p className="text-xs text-muted-foreground">Core tools and technologies</p>
        </div>
      </div>

      {stackItems.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No technologies added yet.</p>
      ) : (
        <div className="mt-4 flex flex-wrap gap-2">
          {stackItems.map((item) => (
            <TagChip key={item} className="rounded-full px-2.5 py-1 text-[12px] text-foreground">
              {item}
            </TagChip>
          ))}
        </div>
      )}
    </Card>
  );
}

export default TechStackCard;
