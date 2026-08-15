import { Card } from "@/components/shared/primitives";
import { GraduationCap } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

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
          <TypoHeading as="h2">Education</TypoHeading>
          <TypoCaption as="p">Academic background</TypoCaption>
        </div>
      </div>

      {education.length === 0 ? (
        <TypoCaption as="p">No education added yet.</TypoCaption>
      ) : (
        <div className="mt-4 space-y-3">
          {education.map((entry) => (
            <div
              key={`${entry.school}-${entry.years ?? "unknown"}`}
              className="rounded-lg border border-border/70 bg-background/70 p-3"
            >
              <p className="text-sm font-semibold text-foreground">{entry.school}</p>
              {entry.degree ? <TypoCaption as="p">{entry.degree}</TypoCaption> : null}
              {entry.years ? <TypoCaption as="p">{entry.years}</TypoCaption> : null}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default EducationCard;
