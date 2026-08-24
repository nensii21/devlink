import React from 'react';
import { GitHubRepository } from '../../lib/github';
import { Star, GitFork, BookMarked } from 'lucide-react';

interface Props {
  repositories: GitHubRepository[] | undefined;
  isLoading: boolean;
}

export const RepositoryStats: React.FC<Props> = ({ repositories, isLoading }) => {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="h-6 w-32 animate-pulse rounded bg-muted" />
          <div className="h-6 w-8 animate-pulse rounded bg-muted" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (!repositories || repositories.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-xl border border-border bg-card p-6 text-muted-foreground">
        <BookMarked className="w-8 h-8 mb-2 opacity-50" />
        <p>No public repositories found.</p>
      </div>
    );
  }

  // Sort by stars, then take top 3
  const topRepos = [...repositories].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 3);

  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-foreground">Popular Repositories</h3>
        <span className="rounded-full bg-primary-soft px-2 py-1 text-xs font-bold text-primary">
          {repositories.length} Total
        </span>
      </div>
      
      <div className="flex flex-col gap-3 flex-1 justify-center">
        {topRepos.map(repo => (
          <a 
            key={repo.id}
            href={repo.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="group block rounded-lg border border-border bg-background p-3 transition-all hover:border-primary/50 hover:shadow-md"
          >
            <div className="flex justify-between items-start mb-1">
              <h4 className="mr-2 truncate font-semibold text-primary group-hover:underline">
                {repo.name}
              </h4>
              <div className="mt-1 flex shrink-0 items-center gap-3 text-xs font-medium text-muted-foreground">
                {repo.stargazers_count > 0 && (
                  <div className="flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                    {repo.stargazers_count}
                  </div>
                )}
                {repo.forks_count > 0 && (
                  <div className="flex items-center gap-1">
                    <GitFork className="w-3.5 h-3.5" />
                    {repo.forks_count}
                  </div>
                )}
              </div>
            </div>
            {repo.description && (
              <p className="text-sm text-surface-500 line-clamp-1 mb-2">
                {repo.description}
              </p>
            )}
            {repo.language && (
              <div className="flex items-center gap-1.5 text-xs text-surface-400 mt-1">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-400"></span>
                {repo.language}
              </div>
            )}
          </a>
        ))}
      </div>
    </div>
  );
};
