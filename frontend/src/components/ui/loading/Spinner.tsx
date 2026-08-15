import React from "react";
import { Loader2 } from "lucide-react";

export interface SpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  color?: "cyan" | "indigo" | "white" | "slate";
  label?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = "md",
  color = "cyan",
  label = "Loading...",
  className = "",
}) => {
  const sizeMap = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
    xl: "w-12 h-12",
  };

  const colorMap = {
    cyan: "text-cyan-500 dark:text-cyan-400",
    indigo: "text-cyan-500 dark:text-cyan-400",
    white: "text-white",
    slate: "text-slate-400",
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`} role="status" aria-label={label}>
      <Loader2 className={`animate-spin ${sizeMap[size]} ${colorMap[color]}`} />
      {label && <span className="sr-only">{label}</span>}
    </div>
  );
};
