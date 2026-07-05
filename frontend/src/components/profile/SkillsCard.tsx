import { Card, TagChip } from "@/components/shared/primitives";
import { Sparkles } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";

export interface SkillsCardProps {
  skills: ProfileSkill[];
}

const levelOrder = ["Beginner", "Intermediate", "Advanced", "Expert"] as const;

function normalizeLevel(level?: string): (typeof levelOrder)[number] {
  const normalized = level?.toLowerCase();
  const match = levelOrder.find((candidate) => candidate.toLowerCase() === normalized);
  return match ?? "Intermediate";
}

export function SkillsCard({ skills }: SkillsCardProps) {
  const groupedSkills = levelOrder
    .map((level) => ({
      level,
      items: skills.filter((skill) => normalizeLevel(skill.level) === level),
    }))
    .filter((group) => group.items.length > 0);

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <Sparkles size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Skills</h2>
          <p className="text-xs text-muted-foreground">Grouped by experience level</p>
        </div>
      </div>

      {groupedSkills.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No skills added yet.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {groupedSkills.map((group) => (
            <div key={group.level}>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {group.level}
              </p>
              <div className="flex flex-wrap gap-2">
                {group.items.map((skill) => (
                  <TagChip key={`${group.level}-${skill.name}`} className="rounded-full px-2.5 py-1 text-[12px] text-foreground">
                    {skill.name}
                    {typeof skill.yearsOfExperience === "number" ? ` · ${skill.yearsOfExperience}y` : ""}
                  </TagChip>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default SkillsCard;
