import React from "react";
import { ShieldCheck, Star, Award, TrendingUp } from "lucide-react";

interface TrustScoreBadgeProps {
  score?: number;
  trustScore?: number;
  trustLevel?: string;
  isVerified?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function TrustScoreBadge({
  score = 0,
  trustScore = 0,
  trustLevel = "Rising Developer 🌱",
  isVerified = false,
  size = "md",
  className = "",
}: TrustScoreBadgeProps) {
  // Normalize trust score if not explicitly passed
  const displayTrust = trustScore > 0 ? trustScore : Math.min(100, Math.round((score / 500) * 100));

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1",
    md: "px-2.5 py-1 text-xs gap-1.5 font-medium",
    lg: "px-3 py-1.5 text-sm gap-2 font-semibold",
  };

  const getBadgeColor = (scoreVal: number) => {
    if (scoreVal >= 85) return "bg-amber-500/10 text-amber-500 border-amber-500/30";
    if (scoreVal >= 60) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/30";
    if (scoreVal >= 30) return "bg-blue-500/10 text-blue-500 border-blue-500/30";
    return "bg-slate-500/10 text-slate-400 border-slate-500/30";
  };

  return (
    <div
      className={`inline-flex items-center rounded-full border transition-colors ${getBadgeColor(
        displayTrust
      )} ${sizeClasses[size]} ${className}`}
      title={`Trust Score: ${displayTrust}/100 • ${trustLevel}`}
    >
      <ShieldCheck className={size === "sm" ? "h-3 w-3" : size === "lg" ? "h-4.5 w-4.5" : "h-3.5 w-3.5"} />
      <span>Trust Score: {displayTrust}%</span>
      {isVerified && (
        <span className="ml-1 inline-flex items-center text-emerald-400" title="Verified Developer Account">
          ✓
        </span>
      )}
    </div>
  );
}
