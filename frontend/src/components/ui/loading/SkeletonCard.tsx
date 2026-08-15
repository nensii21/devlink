import React from 'react';

export interface SkeletonCardProps {
  count?: number;
  className?: string;
  hasAvatar?: boolean;
  lines?: number;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  count = 1,
  className = '',
  hasAvatar = true,
  lines = 3,
}) => {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`} role="status" aria-busy="true" aria-label="Loading content cards">
      {[...Array(count)].map((_, idx) => (
        <div
          key={idx}
          className="p-5 bg-slate-100 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl space-y-4 animate-pulse"
        >
          {hasAvatar && (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-300 dark:bg-slate-700/60 shrink-0"></div>
              <div className="space-y-1.5 flex-1">
                <div className="h-4 bg-slate-300 dark:bg-slate-700/60 rounded w-2/3"></div>
                <div className="h-3 bg-slate-200 dark:bg-slate-700/40 rounded w-1/3"></div>
              </div>
            </div>
          )}
          <div className="space-y-2">
            {[...Array(lines)].map((_, lineIdx) => (
              <div
                key={lineIdx}
                className="h-3.5 bg-slate-200 dark:bg-slate-700/40 rounded"
                style={{ width: lineIdx === lines - 1 ? '60%' : '100%' }}
              ></div>
            ))}
          </div>
          <div className="pt-2 flex items-center justify-between">
            <div className="h-6 bg-slate-200 dark:bg-slate-700/40 rounded-full w-20"></div>
            <div className="h-6 bg-slate-200 dark:bg-slate-700/40 rounded-md w-16"></div>
          </div>
        </div>
      ))}
    </div>
  );
};
