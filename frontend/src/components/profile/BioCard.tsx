import { Card } from "@/components/shared/primitives";
import { MapPin, Clock3, Sparkles } from "lucide-react";

export interface BioCardProps {
  headline?: string | null;
  bio?: string | null;
  location?: string | null;
  timezone?: string | null;
  editable?: boolean;
  formValues?: {
    headline: string;
    bio: string;
    location: string;
    timezone: string;
  };
  errors?: Record<string, string>;
  onFieldChange?: (field: "headline" | "bio" | "location" | "timezone", value: string) => void;
}

export function BioCard({ headline, bio, location, timezone, editable = false, formValues, errors, onFieldChange }: BioCardProps) {
  const hasContent = [headline, bio, location, timezone].some((value) => Boolean(value));
  const bioLength = (editable ? formValues?.bio : bio ?? "").length;

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <Sparkles size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">About</h2>
            <p className="text-xs text-muted-foreground">Update your profile summary</p>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Headline</span>
            <input
              value={formValues?.headline ?? ""}
              onChange={(event) => onFieldChange?.("headline", event.target.value)}
              maxLength={150}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="A short professional headline"
            />
            {errors?.headline ? <p className="mt-1 text-xs text-red-500">{errors.headline}</p> : null}
          </label>

          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Bio</span>
            <textarea
              value={formValues?.bio ?? ""}
              onChange={(event) => onFieldChange?.("bio", event.target.value)}
              maxLength={1000}
              rows={5}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="Tell people about your work and interests"
            />
            <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>{errors?.bio ? <span className="text-red-500">{errors.bio}</span> : "Keep it concise and professional."}</span>
              <span className={bioLength > 1000 ? "text-red-500" : ""}>{bioLength}/1000</span>
            </div>
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Location</span>
              <input
                value={formValues?.location ?? ""}
                onChange={(event) => onFieldChange?.("location", event.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                placeholder="City, Country"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">Timezone</span>
              <input
                value={formValues?.timezone ?? ""}
                onChange={(event) => onFieldChange?.("timezone", event.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                placeholder="e.g. PST"
              />
            </label>
          </div>
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
