import { Card, EmptyState } from "@/components/shared/primitives";
import { Github, Linkedin, ExternalLink } from "lucide-react";
import type { ElementType } from "react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export interface SocialLinksCardProps {
  githubUrl?: string | null;
  linkedinUrl?: string | null;
  portfolioUrl?: string | null;
  website?: string | null;
  editable?: boolean;
  formValues?: {
    githubUrl: string;
    linkedinUrl: string;
    portfolioUrl: string;
    website: string;
  };
  errors?: Record<string, string>;
  onFieldChange?: (
    field: "website" | "portfolioUrl" | "githubUrl" | "linkedinUrl",
    value: string,
  ) => void;
}

interface LinkItem {
  label: string;
  url?: string | null;
  icon: ElementType;
}

export function SocialLinksCard({
  githubUrl,
  linkedinUrl,
  portfolioUrl,
  website,
  editable = false,
  formValues,
  errors,
  onFieldChange,
}: SocialLinksCardProps) {
  const links: LinkItem[] = [
    { label: "GitHub", url: githubUrl, icon: Github },
    { label: "LinkedIn", url: linkedinUrl, icon: Linkedin },
    { label: "Portfolio", url: portfolioUrl ?? website, icon: ExternalLink },
  ].filter((link) => Boolean(link.url));

  if (editable) {
    return (
      <Card className="p-5">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            <ExternalLink size={16} />
          </div>
          <div>
            <TypoHeading as="h2">Social links</TypoHeading>
            <TypoCaption as="p">Add links people can use to reach you</TypoCaption>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {[
            { key: "website", label: "Website", value: formValues?.website ?? "" },
            { key: "portfolioUrl", label: "Portfolio", value: formValues?.portfolioUrl ?? "" },
            { key: "githubUrl", label: "GitHub", value: formValues?.githubUrl ?? "" },
            { key: "linkedinUrl", label: "LinkedIn", value: formValues?.linkedinUrl ?? "" },
          ].map((field) => (
            <label key={field.key} className="block text-sm">
              <TypoCaption>{field.label}</TypoCaption>
              <input
                value={field.value}
                onChange={(event) =>
                  onFieldChange?.(
                    field.key as "website" | "portfolioUrl" | "githubUrl" | "linkedinUrl",
                    event.target.value,
                  )
                }
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground outline-none ring-0 focus:border-primary"
                placeholder="https://example.com"
              />
              {errors?.[field.key] ? (
                <p className="mt-1 text-xs text-red-500">{errors[field.key]}</p>
              ) : null}
            </label>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <ExternalLink size={16} />
        </div>
        <div>
          <TypoHeading as="h2">Social links</TypoHeading>
          <TypoCaption as="p">Find me online</TypoCaption>
        </div>
      </div>

      {links.length === 0 ? (
        <EmptyState
          icon={ExternalLink}
          title="Make it easy to connect"
          desc="Add your GitHub, portfolio, or LinkedIn so collaborators can find your work."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-8"
        />
      ) : (
        <div className="mt-4 flex flex-wrap gap-2">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <a
                key={link.label}
                href={link.url ?? "#"}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
              >
                <Icon size={14} />
                {link.label}
              </a>
            );
          })}
        </div>
      )}
    </Card>
  );
}

export default SocialLinksCard;
