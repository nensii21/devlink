import { Card, EmptyState } from "@/components/shared/primitives";
import { GitFork, Star, ExternalLink, Code2, FolderGit2 } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export interface FeaturedRepo {
  id: string;
  name: string;
  description: string;
  language: string;
  languageColor?: string;
  stars: number;
  forks: number;
  repoUrl?: string;
  liveUrl?: string;
  topics?: string[];
}

export interface FeaturedRepositoriesCardProps {
  repositories?: FeaturedRepo[];
}

const DEFAULT_LANG_COLORS: Record<string, string> = {
  TypeScript: "bg-blue-500",
  JavaScript: "bg-amber-400",
  Python: "bg-emerald-500",
  Rust: "bg-orange-600",
  Go: "bg-cyan-500",
  HTML: "bg-rose-500",
};

export function FeaturedRepositoriesCard({ repositories = [] }: FeaturedRepositoriesCardProps) {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-center justify-between mb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg bg-primary/10 p-2 text-primary">
            <FolderGit2 size={16} />
          </div>
          <div>
            <TypoHeading as="h2">Featured Repositories</TypoHeading>
            <TypoCaption as="p">Pinned open-source projects and codebases</TypoCaption>
          </div>
        </div>
      </div>

      {repositories.length === 0 ? (
        <EmptyState
          icon={FolderGit2}
          title="No featured repositories pinned"
          desc="Pin top GitHub repositories to showcase your open-source work."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-6"
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {repositories.map((repo) => {
            const langDot = DEFAULT_LANG_COLORS[repo.language] || "bg-primary";
            return (
              <div
                key={repo.id}
                className="flex flex-col justify-between rounded-lg border border-border/80 bg-card p-3.5 transition-all hover:border-primary/50 hover:shadow-2xs"
              >
                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <a
                      href={repo.repoUrl || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-bold text-foreground hover:text-primary transition-colors flex items-center gap-1.5 truncate"
                    >
                      <Code2 size={13} className="text-primary shrink-0" />
                      <span className="truncate">{repo.name}</span>
                    </a>
                    {repo.liveUrl && (
                      <a
                        href={repo.liveUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-foreground shrink-0 p-0.5"
                        title="Live Demo"
                      >
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>

                  <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                    {repo.description}
                  </p>

                  {repo.topics && repo.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {repo.topics.slice(0, 3).map((topic) => (
                        <span
                          key={topic}
                          className="rounded-full bg-muted/60 px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-3 mt-2 border-t border-border/50">
                  <div className="flex items-center gap-1.5">
                    <span className={`h-2 w-2 rounded-full ${langDot}`} />
                    <span className="font-medium text-foreground">{repo.language}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Star size={11} className="text-amber-500" /> {repo.stars}
                    </span>
                    <span className="flex items-center gap-1">
                      <GitFork size={11} /> {repo.forks}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

export default FeaturedRepositoriesCard;
