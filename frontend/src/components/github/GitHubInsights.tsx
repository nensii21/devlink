import React from 'react';
import { 
  useGitHubProfile, 
  useGitHubStats, 
  useGitHubRepositories, 
  useGitHubContributions 
} from '../../lib/github';
import { GitHubStats } from './GitHubStats';
import { LanguageStats } from './LanguageStats';
import { RepositoryStats } from './RepositoryStats';
import { ContributionGraph } from './ContributionGraph';
import { Github, ExternalLink } from 'lucide-react';

interface Props {
  username: string;
}

export const GitHubInsights: React.FC<Props> = ({ username }) => {
  // Use parallel queries for performance
  const profileQuery = useGitHubProfile(username);
  const statsQuery = useGitHubStats(username);
  const reposQuery = useGitHubRepositories(username);
  const contributionsQuery = useGitHubContributions(username);

  const isLoading = 
    profileQuery.isLoading || 
    statsQuery.isLoading || 
    reposQuery.isLoading || 
    contributionsQuery.isLoading;

  const isError = 
    profileQuery.isError || 
    statsQuery.isError || 
    reposQuery.isError || 
    contributionsQuery.isError;

  if (isError) {
    return (
      <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-200 flex flex-col items-center justify-center">
        <Github className="w-10 h-10 mb-3 opacity-50" />
        <h3 className="font-semibold text-lg">Unable to load GitHub data</h3>
        <p className="text-sm opacity-80 mt-1">This could be due to rate limiting or an invalid username.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-surface-900 flex items-center gap-2">
          <Github className="w-6 h-6" />
          GitHub Contributions
        </h2>
        {profileQuery.data && (
          <a 
            href={`https://github.com/${username}`} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
          >
            @{username} <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      <ContributionGraph 
        contributions={contributionsQuery.data} 
        isLoading={isLoading} 
      />

      <GitHubStats 
        stats={statsQuery.data} 
        isLoading={isLoading} 
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <RepositoryStats 
            repositories={reposQuery.data} 
            isLoading={isLoading} 
          />
        </div>
        <div className="md:col-span-1">
          <LanguageStats 
            languages={statsQuery.data?.languages} 
            isLoading={isLoading} 
          />
        </div>
      </div>
    </div>
  );
};
