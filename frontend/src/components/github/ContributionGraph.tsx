import React, { useMemo } from 'react';
import { GitHubContribution } from '../../lib/github';

interface Props {
  contributions: GitHubContribution[] | undefined;
  isLoading: boolean;
}

const LEVEL_COLORS = [
  'bg-surface-200',    // 0: No contributions
  'bg-primary-200',    // 1: Light
  'bg-primary-400',    // 2: Medium
  'bg-primary-600',    // 3: High
  'bg-primary-800',    // 4: Very High
];

export const ContributionGraph: React.FC<Props> = ({ contributions, isLoading }) => {
  // If loading, show skeleton graph
  if (isLoading) {
    return (
      <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 overflow-hidden">
        <div className="h-6 w-48 bg-surface-200 rounded animate-pulse mb-6" />
        <div className="flex gap-1 animate-pulse">
          {Array.from({ length: 52 }).map((_, weekIdx) => (
            <div key={weekIdx} className="flex flex-col gap-1">
              {Array.from({ length: 7 }).map((_, dayIdx) => (
                <div key={dayIdx} className="w-3 h-3 rounded-sm bg-surface-200" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!contributions || contributions.length === 0) {
    return null;
  }

  // Organize into weeks (columns)
  const weeks: GitHubContribution[][] = [];
  let currentWeek: GitHubContribution[] = [];

  // GitHub contribution graph typically starts on Sunday.
  // We'll just group them by 7 days.
  contributions.forEach((day, i) => {
    currentWeek.push(day);
    if (currentWeek.length === 7 || i === contributions.length - 1) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });

  // Calculate total
  const totalContributions = contributions.reduce((sum, day) => sum + day.count, 0);

  return (
    <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 overflow-x-auto custom-scrollbar">
      <div className="flex justify-between items-end mb-4 min-w-[700px]">
        <h3 className="text-lg font-semibold text-surface-900">
          {totalContributions.toLocaleString()} contributions in the last year
        </h3>
        <div className="flex items-center gap-1.5 text-xs text-surface-500">
          <span>Less</span>
          {LEVEL_COLORS.map((color, i) => (
            <div key={i} className={`w-3 h-3 rounded-sm ${color}`} />
          ))}
          <span>More</span>
        </div>
      </div>
      
      <div className="flex gap-[3px] min-w-max pb-2">
        {weeks.map((week, wIdx) => (
          <div key={wIdx} className="flex flex-col gap-[3px]">
            {week.map((day, dIdx) => (
              <div
                key={`${wIdx}-${dIdx}`}
                title={`${day.count} contributions on ${day.date}`}
                className={`w-[11px] h-[11px] rounded-[2px] transition-all hover:ring-1 hover:ring-primary-500 hover:scale-125 cursor-crosshair z-10 ${
                  LEVEL_COLORS[Math.min(day.level, 4)]
                }`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};
