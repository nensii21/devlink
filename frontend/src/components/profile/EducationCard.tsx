import { Card } from "@/components/shared/primitives";
import { GraduationCap } from "lucide-react";

export interface EducationEntry {
  school: string;
  degree?: string | null;
  years?: string | null;
}

export interface EducationCardProps {
  education?: EducationEntry[];
}

export function EducationCard({ education = [] }: EducationCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <GraduationCap size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Education</h2>
          <p className="text-xs text-muted-foreground">Academic background</p>
        </div>
      </div>

      {education.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No education added yet.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {education.map((entry) => (
            <div key={`${entry.school}-${entry.years ?? "unknown"}`} className="rounded-lg border border-border/70 bg-background/70 p-3">
              <p className="text-sm font-semibold text-foreground">{entry.school}</p>
              {entry.degree ? <p className="mt-1 text-sm text-muted-foreground">{entry.degree}</p> : null}
              {entry.years ? <p className="mt-1 text-xs text-muted-foreground">{entry.years}</p> : null}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default EducationCard;
