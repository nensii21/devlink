/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import { Card, TagChip } from "@/components/shared/primitives";
import { Sparkles, Plus, Trash2 } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";

export interface SkillsCardProps {
  skills: ProfileSkill[];
  editable?: boolean;
  formValues?: ProfileSkill[];
  skillErrors?: Record<string, string>;
  onSkillChange?: (
    index: number,
    field: "name" | "level" | "category" | "yearsOfExperience",
    value: string | number,
  ) => void;
  onAddSkill?: () => void;
  onRemoveSkill?: (index: number) => void;
}

const levelOrder = ["Beginner", "Intermediate", "Advanced", "Expert"] as const;

function normalizeLevel(level?: string): (typeof levelOrder)[number] {
  const normalized = level?.toLowerCase();
  const match = levelOrder.find((candidate) => candidate.toLowerCase() === normalized);
  return match ?? "Intermediate";
}

const SKILL_CATEGORIES = [
  "Languages",
  "Frameworks",
  "Databases",
  "Cloud",
  "DevOps",
  "AI/ML",
  "Design",
] as const;

export function SkillsCard({
  skills,
  editable = false,
  formValues = [],
  skillErrors = {},
  onSkillChange,
  onAddSkill,
  onRemoveSkill,
}: SkillsCardProps) {
  const categoriesList = SKILL_CATEGORIES;

  const groupedByCategory = categoriesList.map((cat) => ({
    category: cat,
    items: skills.filter((s) => (s.category || "Languages").toLowerCase() === cat.toLowerCase()),
  }));

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Sparkles size={16} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Developer Skill Matrix</h2>
              <p className="text-xs text-muted-foreground">
                Manage your skills across 7 core technical categories
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onAddSkill}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted"
          >
            <Plus size={12} /> Add Skill
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {formValues.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">
              No skills added. Click "Add Skill" to build your matrix.
            </p>
          ) : null}
          {formValues.map((skill, index) => (
            <div
              key={`${skill.name}-${index}`}
              className="rounded-lg border border-border/70 bg-background/60 p-3"
            >
              <div className="grid gap-3 md:grid-cols-[1.5fr_1fr_1fr_auto]">
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                    Skill Name
                  </span>
                  <input
                    value={skill.name}
                    onChange={(event) => onSkillChange?.(index, "name", event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                    placeholder="e.g. TypeScript"
                  />
                </label>
                <label className="text-sm">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                    Proficiency
                  </span>
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
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                    Years Exp.
                  </span>
                  <input
                    type="number"
                    min="0"
                    value={skill.yearsOfExperience ?? 0}
                    onChange={(event) =>
                      onSkillChange?.(index, "yearsOfExperience", Number(event.target.value))
                    }
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => onRemoveSkill?.(index)}
                  className="self-end rounded-md border border-border bg-background p-2 text-muted-foreground hover:bg-muted"
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <label className="mt-3 block text-sm">
                <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                  Category
                </span>
                <select
                  value={skill.category ?? "Languages"}
                  onChange={(event) => onSkillChange?.(index, "category", event.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                >
                  {SKILL_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </label>
              {skillErrors?.[`${index}`] ? (
                <p className="mt-2 text-xs text-red-500">{skillErrors[`${index}`]}</p>
              ) : null}
            </div>
          ))}
          {skillErrors?.skills ? (
            <p className="text-xs text-red-500">{skillErrors.skills}</p>
          ) : null}
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 w-full">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-primary/10 p-2 text-primary">
            <Sparkles size={18} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">Developer Skill Matrix</h2>
            <p className="text-xs text-muted-foreground">
              Categorized technical expertise and proficiency
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
        {groupedByCategory.map(({ category, items }) => (
          <div
            key={category}
            className="rounded-lg border border-border bg-muted/20 p-3.5 flex flex-col justify-between space-y-2 hover:border-primary/30 transition-colors"
          >
            <div>
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-border/40">
                <span className="text-xs font-bold uppercase tracking-wider text-primary">
                  {category}
                </span>
                <span className="text-[10px] text-muted-foreground font-medium rounded bg-muted px-1.5 py-0.5">
                  {items.length} {items.length === 1 ? "skill" : "skills"}
                </span>
              </div>
              {items.length === 0 ? (
                <p className="text-xs text-muted-foreground/60 italic py-1">No skills added</p>
              ) : (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {items.map((skill) => (
                    <span
                      key={`${category}-${skill.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2.5 py-1 text-xs font-medium text-foreground shadow-sm"
                    >
                      <span>{skill.name}</span>
                      <span className="text-[10px] font-normal text-muted-foreground bg-muted/60 px-1 py-0.2 rounded">
                        {skill.level || "Intermediate"}
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default SkillsCard;
