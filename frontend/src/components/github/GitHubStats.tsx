import React from 'react';
import { GitHubStats as IGitHubStats } from '../../lib/github';

interface Props {
  stats: IGitHubStats | undefined;
  isLoading: boolean;
}

export const GitHubStats: React.FC<Props> = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-surface-100 rounded-xl" />
        ))}
      </div>
    );
  }

  const items = [
    { label: 'Pull Requests', value: stats?.total_prs ?? 0, icon: '🚀' },
    { label: 'Issues', value: stats?.total_issues ?? 0, icon: '🐛' },
    { label: 'Stars', value: stats?.total_stars ?? 0, icon: '⭐' },
    { label: 'Followers', value: stats?.followers ?? 0, icon: '👥' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {items.map((item, i) => (
        <div 
          key={i} 
          className="bg-surface-50 border border-surface-200 p-4 rounded-xl flex flex-col items-center justify-center gap-1 hover:border-primary-500 hover:shadow-sm transition-all duration-300 transform hover:-translate-y-1"
        >
          <div className="text-2xl mb-1">{item.icon}</div>
          <div className="text-2xl font-bold text-surface-900">{item.value.toLocaleString()}</div>
          <div className="text-sm text-surface-500 font-medium">{item.label}</div>
        </div>
      ))}
    </div>
  );
};
