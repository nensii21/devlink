import React from 'react';

export interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

export const SkeletonTable: React.FC<SkeletonTableProps> = ({
  rows = 5,
  columns = 4,
  className = '',
}) => {
  return (
    <div className={`w-full overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 p-4 ${className}`} role="status" aria-busy="true" aria-label="Loading data table">
      <div className="animate-pulse space-y-4">
        <div className="grid gap-4 pb-3 border-b border-slate-200 dark:border-slate-800" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
          {[...Array(columns)].map((_, cIdx) => (
            <div key={cIdx} className="h-4 bg-slate-300 dark:bg-slate-700/60 rounded w-3/4"></div>
          ))}
        </div>

        {[...Array(rows)].map((_, rIdx) => (
          <div
            key={rIdx}
            className="grid gap-4 py-2.5 items-center border-b border-slate-200/60 dark:border-slate-800/40 last:border-none"
            style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
          >
            {[...Array(columns)].map((_, cIdx) => (
              <div
                key={cIdx}
                className="h-3.5 bg-slate-200 dark:bg-slate-700/40 rounded"
                style={{ width: cIdx === 0 ? '80%' : cIdx === columns - 1 ? '50%' : '65%' }}
              ></div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};
