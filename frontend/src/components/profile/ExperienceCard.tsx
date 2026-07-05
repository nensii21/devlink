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
}

export function ExperienceCard({ role, company, experienceLevel, entries }: ExperienceCardProps) {
  const fallbackEntries = role || company || experienceLevel
    ? [{ title: role, company, experienceLevel }]
    : [];
  const experienceEntries = (entries?.filter((entry) => Boolean(entry.title || entry.company || entry.experienceLevel)) ?? []).length
    ? entries?.filter((entry) => Boolean(entry.title || entry.company || entry.experienceLevel)) ?? []
    : fallbackEntries;

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
