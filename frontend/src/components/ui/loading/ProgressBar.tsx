import React from "react";

export interface ProgressBarProps {
  progress?: number;
  indeterminate?: boolean;
  showLabel?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress = 0,
  indeterminate = false,
  showLabel = false,
  className = "",
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div
      className={`w-full space-y-1.5 ${className}`}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={indeterminate ? undefined : clampedProgress}
      aria-label="Progress bar"
    >
      {showLabel && !indeterminate && (
        <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
          <span>Progress</span>
          <span>{clampedProgress}%</span>
        </div>
      )}
      <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden border border-slate-300/60 dark:border-slate-700/60">
        {indeterminate ? (
          <div className="h-full bg-gradient-to-r from-cyan-500 via-teal-400 to-cyan-500 rounded-full animate-pulse w-full"></div>
        ) : (
          <div
            className="h-full bg-cyan-500 dark:bg-cyan-400 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${clampedProgress}%` }}
          ></div>
        )}
      </div>
    </div>
  );
};
