import React from 'react';
import { GitHubLanguage } from '../../lib/github';

interface Props {
  languages: GitHubLanguage[] | undefined;
  isLoading: boolean;
}

const COLORS = ['bg-primary-500', 'bg-blue-500', 'bg-emerald-500', 'bg-amber-500', 'bg-purple-500'];

export const LanguageStats: React.FC<Props> = ({ languages, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-surface-50 p-6 rounded-xl border border-surface-200">
        <div className="h-6 w-32 bg-surface-200 rounded animate-pulse mb-6" />
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex flex-col gap-2">
              <div className="flex justify-between">
                <div className="h-4 w-20 bg-surface-200 rounded" />
                <div className="h-4 w-10 bg-surface-200 rounded" />
              </div>
              <div className="h-2 w-full bg-surface-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!languages || languages.length === 0) {
    return null;
  }

  return (
    <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 h-full flex flex-col">
      <h3 className="text-lg font-semibold text-surface-900 mb-4">Top Languages</h3>
      <div className="space-y-5 flex-1 justify-center flex flex-col">
        {languages.map((lang, index) => (
          <div key={lang.name} className="flex flex-col gap-1.5 group">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-surface-700 group-hover:text-primary-600 transition-colors">
                {lang.name}
              </span>
              <span className="text-surface-500 font-mono">
                {lang.percentage}%
              </span>
            </div>
            <div className="h-2 w-full bg-surface-200 rounded-full overflow-hidden">
              <div 
                className={`h-full ${COLORS[index % COLORS.length]} transition-all duration-1000 ease-out`} 
                style={{ width: `${lang.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
