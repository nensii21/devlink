import { Card, TagChip } from "@/components/shared/primitives";
import { Sparkles, Plus, Trash2 } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";

export interface SkillsCardProps {
  skills: ProfileSkill[];
  editable?: boolean;
  formValues?: ProfileSkill[];
  skillErrors?: Record<string, string>;
  onSkillChange?: (index: number, field: "name" | "level" | "category" | "yearsOfExperience", value: string | number) => void;
  onAddSkill?: () => void;
  onRemoveSkill?: (index: number) => void;
}

const levelOrder = ["Beginner", "Intermediate", "Advanced", "Expert"] as const;

function normalizeLevel(level?: string): (typeof levelOrder)[number] {
  const normalized = level?.toLowerCase();
  const match = levelOrder.find((candidate) => candidate.toLowerCase() === normalized);
  return match ?? "Intermediate";
}

export function SkillsCard({ skills, editable = false, formValues = [], skillErrors = {}, onSkillChange, onAddSkill, onRemoveSkill }: SkillsCardProps) {
  const groupedSkills = levelOrder
    .map((level) => ({
      level,
      items: skills.filter((skill) => normalizeLevel(skill.level) === level),
    }))
    .filter((group) => group.items.length > 0);

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Sparkles size={16} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Skills</h2>
              <p className="text-xs text-muted-foreground">Add and organize your skills</p>
            </div>
          </div>
          <button type="button" onClick={onAddSkill} className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted">
            <Plus size={12} /> Add
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {formValues.length === 0 ? <p className="text-sm text-muted-foreground">No skills added yet.</p> : null}
          {formValues.map((skill, index) => (
            <div key={`${skill.name}-${index}`} className="rounded-lg border border-border/70 bg-background/60 p-3">
              <div className="grid gap-3 md:grid-cols-[1.5fr_1fr_1fr_auto]">
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Skill</span>
                  <input
                    value={skill.name}
                    onChange={(event) => onSkillChange?.(index, "name", event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                    placeholder="e.g. React"
                  />
                </label>
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Level</span>
                  <select
                    value={skill.level ?? "Intermediate"}
                    onChange={(event) => onSkillChange?.(index, "level", event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                  >
                    {levelOrder.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Years</span>
                  <input
                    type="number"
                    min="0"
                    value={skill.yearsOfExperience ?? 0}
                    onChange={(event) => onSkillChange?.(index, "yearsOfExperience", Number(event.target.value))}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                  />
                </label>
                <button type="button" onClick={() => onRemoveSkill?.(index)} className="self-end rounded-md border border-border bg-background p-2 text-muted-foreground hover:bg-muted">
                  <Trash2 size={14} />
                </button>
              </div>
              <label className="mt-3 block text-sm">
                <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Category</span>
                <input
                  value={skill.category ?? "general"}
                  onChange={(event) => onSkillChange?.(index, "category", event.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                  placeholder="frontend, backend, devops"
                />
              </label>
              {skillErrors?.[`${index}`] ? <p className="mt-2 text-xs text-red-500">{skillErrors[`${index}`]}</p> : null}
            </div>
          ))}
          {skillErrors?.skills ? <p className="text-xs text-red-500">{skillErrors.skills}</p> : null}
        </div>
      </Card>
    );
  }

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
