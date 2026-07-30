import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  desc?: string;
  action?: ReactNode;
  icon?: React.ComponentType<{ className?: string; size?: number }>;
  illustration?: "empty-box" | "no-results" | "no-messages" | "no-notifications" | "no-bookmarks" | "no-projects";
  className?: string;
}

export function EmptyState({
  title,
  desc,
  action,
  icon: Icon,
  illustration,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-center animate-in fade-in duration-200", className)}>
      <div className="mb-4">
        {illustration ? (
          <EmptyIllustration variant={illustration} />
        ) : (
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-primary-soft text-primary shadow-xs">
            {Icon ? <Icon size={24} /> : "✨"}
          </div>
        )}
      </div>
      <p className="text-[14px] font-semibold text-foreground">{title}</p>
      {desc && <p className="mt-1 max-w-xs text-[13px] text-muted-foreground">{desc}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

function EmptyIllustration({ variant }: { variant: string }) {
  return (
    <svg
      width="120"
      height="100"
      viewBox="0 0 120 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="animate-in zoom-in-50 duration-300"
    >
      {variant === "empty-box" && (
        <>
          <rect x="30" y="30" width="60" height="50" rx="6" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.3" />
          <rect x="40" y="40" width="40" height="30" rx="4" stroke="var(--primary)" strokeWidth="2" opacity="0.4" />
          <line x1="50" y1="50" x2="70" y2="50" stroke="var(--primary)" strokeWidth="2" opacity="0.3" strokeLinecap="round" />
          <line x1="50" y1="58" x2="65" y2="58" stroke="var(--primary)" strokeWidth="2" opacity="0.2" strokeLinecap="round" />
          <circle cx="35" cy="25" r="3" fill="var(--primary)" opacity="0.2" />
          <circle cx="85" cy="22" r="2" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-results" && (
        <>
          <circle cx="50" cy="45" r="25" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" />
          <line x1="68" y1="63" x2="80" y2="75" stroke="var(--muted-foreground)" strokeWidth="3" opacity="0.2" strokeLinecap="round" />
          <line x1="42" y1="42" x2="58" y2="42" stroke="var(--primary)" strokeWidth="2" opacity="0.3" strokeLinecap="round" />
          <line x1="42" y1="50" x2="54" y2="50" stroke="var(--primary)" strokeWidth="2" opacity="0.2" strokeLinecap="round" />
          <circle cx="35" cy="25" r="3" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-messages" && (
        <>
          <rect x="25" y="25" width="70" height="40" rx="8" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" />
          <path d="M40 35 L55 35 M40 45 L65 45 M40 55 L50 55" stroke="var(--primary)" strokeWidth="2" opacity="0.3" strokeLinecap="round" />
          <circle cx="35" cy="20" r="2" fill="var(--primary)" opacity="0.15" />
          <circle cx="88" cy="22" r="2.5" fill="var(--primary)" opacity="0.2" />
        </>
      )}
      {variant === "no-notifications" && (
        <>
          <path d="M50 25 C42 25 38 30 38 38 L38 55 L32 55 L68 55 L62 55 L62 38 C62 30 58 25 50 25" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" strokeLinejoin="round" />
          <circle cx="50" cy="68" r="4" stroke="var(--primary)" strokeWidth="2" opacity="0.3" />
          <circle cx="35" cy="22" r="2" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-bookmarks" && (
        <>
          <path d="M35 25 L35 70 L50 58 L65 70 L65 25 Z" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" strokeLinejoin="round" />
          <line x1="42" y1="35" x2="58" y2="35" stroke="var(--primary)" strokeWidth="2" opacity="0.2" strokeLinecap="round" />
          <circle cx="30" cy="22" r="2.5" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-projects" && (
        <>
          <rect x="30" y="25" width="25" height="25" rx="4" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.25" />
          <rect x="65" y="30" width="25" height="25" rx="4" stroke="var(--primary)" strokeWidth="2" opacity="0.3" />
          <rect x="45" y="60" width="25" height="25" rx="4" stroke="var(--muted-foreground)" strokeWidth="2" opacity="0.2" />
          <circle cx="35" cy="20" r="2" fill="var(--primary)" opacity="0.15" />
          <circle cx="90" cy="22" r="2" fill="var(--primary)" opacity="0.1" />
        </>
      )}
    </svg>
  );
}
