import { Card, EmptyState } from "@/components/shared/primitives";
import { FolderGit2, ExternalLink, Globe, Sparkles } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export interface PortfolioItem {
  id: string;
  title: string;
  description: string;
  link?: string;
  role?: string;
  image?: string;
  tags?: string[];
  year?: string;
}

export interface PortfolioShowcaseCardProps {
  items?: PortfolioItem[];
}

export function PortfolioShowcaseCard({ items = [] }: PortfolioShowcaseCardProps) {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-500">
            <Globe size={16} />
          </div>
          <div>
            <TypoHeading as="h2">Portfolio & Highlights</TypoHeading>
            <TypoCaption as="p">Key products, client works, and shipped systems</TypoCaption>
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={Globe}
          title="No portfolio items showcased yet"
          desc="Showcase published apps, products, and case studies."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-6"
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-lg border border-border/80 bg-card p-3.5 transition-all hover:border-primary/40 hover:shadow-2xs"
            >
              <div className="space-y-2">
                {item.image && (
                  <div className="h-28 w-full overflow-hidden rounded-md bg-muted border border-border">
                    <img
                      src={item.image}
                      alt={item.title}
                      className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
                    />
                  </div>
                )}

                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs font-bold text-foreground">{item.title}</p>
                    {item.role && (
                      <p className="text-[10px] font-semibold text-primary">{item.role}</p>
                    )}
                  </div>
                  {item.link && (
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-[10px] font-medium text-foreground hover:bg-muted/80 transition-colors shrink-0"
                    >
                      <span>Visit</span>
                      <ExternalLink size={9} />
                    </a>
                  )}
                </div>

                <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                  {item.description}
                </p>

                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded bg-muted/60 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {item.year && (
                <div className="pt-2 mt-2 border-t border-border/50 text-[10px] text-muted-foreground">
                  Shipped {item.year}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default PortfolioShowcaseCard;
