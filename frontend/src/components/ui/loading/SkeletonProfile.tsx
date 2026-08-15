import React from 'react';

export interface SkeletonProfileProps {
  className?: string;
}

export const SkeletonProfile: React.FC<SkeletonProfileProps> = ({ className = '' }) => {
  return (
    <div
      className={`w-full max-w-4xl p-6 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl space-y-6 animate-pulse shadow-sm dark:shadow-none ${className}`}
      role="status"
      aria-busy="true"
      aria-label="Loading developer profile"
    >
      <div className="relative">
        <div className="w-full h-36 bg-slate-200 dark:bg-slate-800/60 rounded-xl"></div>
        <div className="absolute -bottom-8 left-6 w-20 h-20 rounded-full border-4 border-white dark:border-slate-900 bg-slate-300 dark:bg-slate-700/80"></div>
      </div>

      <div className="pt-6 space-y-3">
        <div className="h-6 bg-slate-300 dark:bg-slate-700/60 rounded w-1/3"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-700/40 rounded w-1/4"></div>
        <div className="h-3.5 bg-slate-200 dark:bg-slate-700/40 rounded w-2/3"></div>
      </div>

      <div className="flex gap-2 pt-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-7 bg-slate-200 dark:bg-slate-800 rounded-full w-20"></div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
        <div className="h-28 bg-slate-100 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl"></div>
        <div className="h-28 bg-slate-100 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl"></div>
      </div>
    </div>
  );
};
