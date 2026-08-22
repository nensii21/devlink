import { Card, EmptyState } from "@/components/shared/primitives";
import { MapPin, Clock3, Sparkles } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

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

export function BioCard({
  headline,
  bio,
  location,
  timezone,
  editable = false,
  formValues,
  errors,
  onFieldChange,
}: BioCardProps) {
  const hasContent = [headline, bio, location, timezone].some((value) => Boolean(value));
  const bioLength = (editable ? (formValues?.bio ?? "") : (bio ?? "")).length;

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <Sparkles size={16} />
          </div>
          <div>
            <TypoHeading as="h2">About</TypoHeading>
            <TypoCaption as="p">Update your profile summary</TypoCaption>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          <label className="block text-sm">
            <TypoCaption>Headline</TypoCaption>
            <input
              value={formValues?.headline ?? ""}
              onChange={(event) => onFieldChange?.("headline", event.target.value)}
              maxLength={150}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="A short professional headline"
            />
            {errors?.headline ? (
              <p className="mt-1 text-xs text-red-500">{errors.headline}</p>
            ) : null}
          </label>

          <label className="block text-sm">
            <TypoCaption>Bio</TypoCaption>
            <textarea
              value={formValues?.bio ?? ""}
              onChange={(event) => onFieldChange?.("bio", event.target.value)}
              maxLength={1000}
              rows={5}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
              placeholder="Tell people about your work and interests"
            />
            <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {errors?.bio ? (
                  <span className="text-red-500">{errors.bio}</span>
                ) : (
                  "Keep it concise and professional."
                )}
              </span>
              <span className={bioLength > 1000 ? "text-red-500" : ""}>{bioLength}/1000</span>
            </div>
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              <TypoCaption>Location</TypoCaption>
              <input
                value={formValues?.location ?? ""}
                onChange={(event) => onFieldChange?.("location", event.target.value)}
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                placeholder="City, Country"
              />
            </label>
            <label className="block text-sm">
              <TypoCaption>Timezone</TypoCaption>
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
          <TypoHeading as="h2">About</TypoHeading>
          <TypoCaption as="p">Profile summary</TypoCaption>
        </div>
      </div>

      {!hasContent ? (
        <EmptyState
          icon={Sparkles}
          title="Tell your story"
          desc="Add a short bio, headline, or location to help other builders get to know you."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-8"
        />
      ) : (
        <div className="mt-4 space-y-3">
          {headline ? <p className="text-sm font-semibold text-foreground">{headline}</p> : null}
          {bio ? <TypoCaption as="p">{bio}</TypoCaption> : null}

          <div className="flex flex-wrap gap-2">
            {location ? (
              <TypoCaption>
                <MapPin size={12} /> {location}
              </TypoCaption>
            ) : null}
            {timezone ? (
              <TypoCaption>
                <Clock3 size={12} /> {timezone}
              </TypoCaption>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  );
}

export default BioCard;
