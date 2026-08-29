import { Card, EmptyState } from "@/components/shared/primitives";
import { GraduationCap } from "lucide-react";
import { TypoCaption } from "@/components/shared/Typography";

export interface EducationEntry {
  school: string;
  degree?: string;
  years?: string;
}

export interface EducationCardProps {
  education?: EducationEntry[];
}

export function EducationCard({ education = [] }: EducationCardProps) {
  const hasContent = education.length > 0;

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

      {!hasContent ? (
        <EmptyState
          icon={GraduationCap}
          title="Add your learning journey"
          desc="Share the education and training that shaped your path."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-8"
        />
      ) : (
        <div className="mt-4 space-y-3">
          {education.map((entry) => (
            <div
              key={`${entry.school}-${entry.years ?? "unknown"}`}
              className="rounded-lg border border-border/70 bg-background/70 p-3"
            >
              <p className="text-sm font-semibold text-foreground">{entry.school}</p>
              {entry.degree ? (
                <TypoCaption as="p" className="mt-1 text-sm text-muted-foreground">
                  {entry.degree}
                </TypoCaption>
              ) : null}
              {entry.years ? (
                <TypoCaption as="p" className="mt-1 text-xs text-muted-foreground">
                  {entry.years}
                </TypoCaption>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default EducationCard;
