import { Card } from "@/components/shared/primitives";
import { BriefcaseBusiness, BadgeCheck } from "lucide-react";

export interface ExperienceEntry {
  title?: string | null;
  company?: string | null;
  experienceLevel?: string | null;
  period?: string | null;
  description?: string | null;
}

export interface ExperienceCardProps {
  role?: string | null;
  company?: string | null;
  experienceLevel?: string | null;
  entries?: ExperienceEntry[];
  editable?: boolean;
  formValues?: {
    role: string;
    company: string;
    experienceLevel: string;
  };
  errors?: Record<string, string>;
  onFieldChange?: (field: "role" | "company" | "experienceLevel", value: string) => void;
}

export function ExperienceCard({ role, company, experienceLevel, entries, editable = false, formValues, errors, onFieldChange }: ExperienceCardProps) {
  const fallbackEntries = role || company || experienceLevel
    ? [{ title: role, company, experienceLevel }]
    : [];
  const experienceEntries = (entries?.filter((entry) => Boolean(entry.title || entry.company || entry.experienceLevel)) ?? []).length
    ? entries?.filter((entry) => Boolean(entry.title || entry.company || entry.experienceLevel)) ?? []
    : fallbackEntries;

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <BriefcaseBusiness size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Experience</h2>
            <p className="text-xs text-muted-foreground">Share your current role and background</p>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Role</span>
            <input
              value={formValues?.role ?? ""}
              onChange={(event) => onFieldChange?.("role", event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="Senior Product Engineer"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Company</span>
            <input
              value={formValues?.company ?? ""}
              onChange={(event) => onFieldChange?.("company", event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="Northstar Labs"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Experience Level</span>
            <input
              value={formValues?.experienceLevel ?? ""}
              onChange={(event) => onFieldChange?.("experienceLevel", event.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="Senior / Lead"
            />
            {errors?.experienceLevel ? <p className="mt-1 text-xs text-red-500">{errors.experienceLevel}</p> : null}
          </label>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <BriefcaseBusiness size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Experience</h2>
          <p className="text-xs text-muted-foreground">Current role and background</p>
        </div>
      </div>

      {experienceEntries.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No experience added yet.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {experienceEntries.map((entry, index) => (
            <div key={`${entry.title ?? "role"}-${index}`} className="relative pl-5">
              <span className="absolute left-0 top-1.5 h-2.5 w-2.5 rounded-full bg-primary" />
              <div className="border-l border-border/70 pl-4">
                <p className="text-sm font-semibold text-foreground">{entry.title ?? role ?? "Current role"}</p>
                <p className="mt-1 text-sm text-muted-foreground">{entry.company ?? company ?? "Independent"}</p>
                {entry.experienceLevel || experienceLevel ? (
                  <div className="mt-2 inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                    <BadgeCheck size={12} /> {entry.experienceLevel ?? experienceLevel}
                  </div>
                ) : null}
                {entry.period ? <p className="mt-2 text-xs text-muted-foreground">{entry.period}</p> : null}
                {entry.description ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{entry.description}</p> : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default ExperienceCard;
