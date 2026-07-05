import { Card } from "@/components/shared/primitives";
import { Github, Linkedin, ExternalLink } from "lucide-react";

export interface SocialLinksCardProps {
  githubUrl?: string | null;
  linkedinUrl?: string | null;
  portfolioUrl?: string | null;
  website?: string | null;
}

interface LinkItem {
  label: string;
  url?: string | null;
  icon: React.ElementType;
}

export function SocialLinksCard({ githubUrl, linkedinUrl, portfolioUrl, website }: SocialLinksCardProps) {
  const links: LinkItem[] = [
    { label: "GitHub", url: githubUrl, icon: Github },
    { label: "LinkedIn", url: linkedinUrl, icon: Linkedin },
    { label: "Portfolio", url: portfolioUrl ?? website, icon: ExternalLink },
  ].filter((link) => Boolean(link.url));

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <ExternalLink size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">Social links</h2>
          <p className="text-xs text-muted-foreground">Find me online</p>
        </div>
      </div>

      {links.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">No links added yet.</p>
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
