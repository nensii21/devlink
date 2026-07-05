import { Card } from "@/components/shared/primitives";
import { MapPin, Clock3, Sparkles } from "lucide-react";

export interface BioCardProps {
  headline?: string | null;
  bio?: string | null;
  location?: string | null;
  timezone?: string | null;
}

export function BioCard({ headline, bio, location, timezone }: BioCardProps) {
  const hasContent = [headline, bio, location, timezone].some((value) => Boolean(value));

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <Sparkles size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">About</h2>
          <p className="text-xs text-muted-foreground">Profile summary</p>
        </div>
      </div>

      {!hasContent ? (
        <p className="mt-4 text-sm text-muted-foreground">No profile details added yet.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {headline ? <p className="text-sm font-semibold text-foreground">{headline}</p> : null}
          {bio ? <p className="text-sm leading-6 text-muted-foreground">{bio}</p> : null}

          <div className="flex flex-wrap gap-2">
            {location ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                <MapPin size={12} /> {location}
              </span>
            ) : null}
            {timezone ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                <Clock3 size={12} /> {timezone}
              </span>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  );
}

export default BioCard;
