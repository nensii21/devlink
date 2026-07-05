import { Card, TagChip } from "@/components/shared/primitives";
import { Cpu } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";

export interface TechStackCardProps {
  skills?: ProfileSkill[];
  techStack?: string[];
}

export function TechStackCard({ skills = [], techStack }: TechStackCardProps) {
  const resolvedStack = (techStack?.filter(Boolean) ?? []).length
    ? techStack?.filter(Boolean) ?? []
    : skills.filter((skill) => Boolean(skill.category)).map((skill) => skill.name);

  const fallbackStack = resolvedStack.length === 0 ? skills.map((skill) => skill.name) : [];
  const stackItems = resolvedStack.length > 0 ? resolvedStack : fallbackStack;

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
