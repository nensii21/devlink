import { Card, EmptyState } from "@/components/shared/primitives";
import { Sparkles, Plus, Trash2 } from "lucide-react";
import type { ProfileSkill } from "@/mocks/seed";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import type { ReactNode } from "react";

export interface SkillsCardProps {
  skills: ProfileSkill[];
  editable?: boolean;
  isOwnProfile?: boolean;
  onManageSkills?: () => void;
  formValues?: ProfileSkill[];
  skillErrors?: Record<string, string>;
  onSkillChange?: (
    index: number,
    field: "name" | "level" | "category" | "yearsOfExperience",
    value: string | number,
  ) => void;
  onAddSkill?: () => void;
  onRemoveSkill?: (index: number) => void;
  emptyAction?: ReactNode;
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
  isOwnProfile = false,
  onManageSkills,
  formValues = [],
  skillErrors = {},
  onSkillChange,
  onAddSkill,
  onRemoveSkill,
  emptyAction,
}: SkillsCardProps) {
  const categoriesList = SKILL_CATEGORIES;

  const groupedByCategory = categoriesList
    .map((cat) => ({
      category: cat,
      items: skills.filter(
        (skill) => (skill.category || "Languages").toLowerCase() === cat.toLowerCase(),
      ),
    }))
    .filter(({ items }) => items.length > 0);

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Sparkles size={16} />
            </div>
            <div>
              <TypoHeading as="h2">Developer Skill Matrix</TypoHeading>
              <TypoCaption as="p">
                Manage your skills across 7 core technical categories
              </TypoCaption>
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
            <TypoCaption as="p">
              No skills added. Click "Add Skill" to build your matrix.
            </TypoCaption>
          ) : null}
          {formValues.map((skill, index) => (
            <div
              key={`${skill.name}-${index}`}
              className="rounded-lg border border-border/70 bg-background/60 p-3"
            >
              <div className="grid gap-3 md:grid-cols-[1.5fr_1fr_1fr_auto]">
                <label className="text-sm">
                  <TypoCaption>Skill Name</TypoCaption>
                  <input
                    value={skill.name}
                    onChange={(event) => onSkillChange?.(index, "name", event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                    placeholder="e.g. TypeScript"
                  />
                </label>
                <label className="text-sm">
                  <TypoCaption>Proficiency</TypoCaption>
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
                  <TypoCaption>Years Exp.</TypoCaption>
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
                <TypoCaption>Category</TypoCaption>
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
            <TypoHeading as="h2">Developer Skill Matrix</TypoHeading>
            <TypoCaption as="p">Categorized technical expertise and proficiency</TypoCaption>
          </div>
        </div>
        {onManageSkills && (
          <button
            type="button"
            onClick={onManageSkills}
            className="inline-flex items-center gap-1 rounded-md bg-primary/10 hover:bg-primary/20 text-primary px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer"
          >
            Manage Skills
          </button>
        )}
      </div>

      {skills.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="Show off what you build with"
          desc="Add your languages, frameworks, and tools so collaborators can find the right fit."
          action={emptyAction}
          className="py-9"
        />
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {groupedByCategory.map(({ category, items }) => (
            <div
              key={category}
              className="flex flex-col justify-between space-y-2 rounded-lg border border-border bg-muted/20 p-3.5 transition-colors hover:border-primary/30"
            >
              <div>
                <div className="mb-2 flex items-center justify-between border-b border-border/40 pb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-primary">
                    {category}
                  </span>
                  <TypoCaption>
                    {items.length} {items.length === 1 ? "skill" : "skills"}
                  </TypoCaption>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {items.map((skill) => (
                    <span
                      key={`${category}-${skill.name}`}
                      className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2.5 py-1 text-xs font-medium text-foreground shadow-sm"
                    >
                      <span>{skill.name}</span>
                      <TypoCaption>{skill.level || "Intermediate"}</TypoCaption>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default SkillsCard;
