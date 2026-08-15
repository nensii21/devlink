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
      <div className="bg-surface-50 p-6 rounded-xl border border-surface-200">
        <div className="flex justify-between items-center mb-6">
          <div className="h-6 w-32 bg-surface-200 rounded animate-pulse" />
          <div className="h-6 w-8 bg-surface-200 rounded animate-pulse" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-surface-200 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!repositories || repositories.length === 0) {
    return (
      <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 h-full flex flex-col items-center justify-center text-surface-500">
        <BookMarked className="w-8 h-8 mb-2 opacity-50" />
        <p>No public repositories found.</p>
      </div>
    );
  }

  // Sort by stars, then take top 3
  const topRepos = [...repositories].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 3);

  return (
    <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-surface-900">Popular Repositories</h3>
        <span className="bg-primary-100 text-primary-700 text-xs font-bold px-2 py-1 rounded-full">
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
            className="block p-3 bg-white border border-surface-200 rounded-lg hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <div className="flex justify-between items-start mb-1">
              <h4 className="font-semibold text-primary-600 truncate mr-2 group-hover:underline">
                {repo.name}
              </h4>
              <div className="flex items-center gap-3 text-xs text-surface-500 font-medium shrink-0 mt-1">
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
