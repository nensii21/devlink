import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { FolderKanban, BellOff, MessageSquareDashed, UserPlus, Search } from "lucide-react";

export function SectionHeader({
  title,
  action,
  actionTo,
  className,
}: {
  title: string;
  action?: string;
  actionTo?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center justify-between px-4 pt-4 pb-3", className)}>
      <h3 className="text-[14px] font-semibold text-foreground">{title}</h3>
      {action &&
        (actionTo ? (
          <Link to={actionTo} className="text-[12px] font-medium text-primary hover:underline">
            {action}
          </Link>
        ) : (
          <button className="text-[12px] font-medium text-primary hover:underline">{action}</button>
        ))}
    </div>
  );
}

export function Card({
  children,
  className,
  as: As = "div",
  interactive = false,
}: {
  children?: ReactNode;
  className?: string;
  as?: "div" | "article" | "section";
  interactive?: boolean;
}) {
  return (
    <As
      className={cn(
        "rounded-md border border-border bg-card shadow-soft",
        interactive && "transition-shadow hover:shadow-card",
        className,
      )}
    >
      {children}
    </As>
  );
}

export function EmptyState({
  title,
  desc,
  action,
  variant = "default",
  className,
}: {
  title: string;
  desc?: string;
  action?: ReactNode;
  variant?: "projects" | "notifications" | "messages" | "connections" | "search" | "default";
  className?: string;
}) {
  const renderIllustration = () => {
    switch (variant) {
      case "projects":
        return (
          <div className="group relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-primary shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-card">
            <FolderKanban className="h-10 w-10 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3" />
            <div className="absolute -inset-4 rounded-full bg-primary opacity-5 blur-xl pointer-events-none transition-all duration-300 group-hover:opacity-10 group-hover:scale-110" />
          </div>
        );
      case "notifications":
        return (
          <div className="group relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-amber-500/10 to-orange-500/10 border border-amber-500/20 text-warning shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-card">
            <BellOff className="h-10 w-10 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6" />
            <div className="absolute -inset-4 rounded-full bg-warning opacity-5 blur-xl pointer-events-none transition-all duration-300 group-hover:opacity-10 group-hover:scale-110" />
          </div>
        );
      case "messages":
        return (
          <div className="group relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 text-indigo-500 shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-card">
            <MessageSquareDashed className="h-10 w-10 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-[-6deg]" />
            <div className="absolute -inset-4 rounded-full bg-indigo-500 opacity-5 blur-xl pointer-events-none transition-all duration-300 group-hover:opacity-10 group-hover:scale-110" />
          </div>
        );
      case "connections":
        return (
          <div className="group relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 text-success shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-card">
            <UserPlus className="h-10 w-10 transition-transform duration-300 group-hover:scale-110 group-hover:-translate-y-0.5" />
            <div className="absolute -inset-4 rounded-full bg-success opacity-5 blur-xl pointer-events-none transition-all duration-300 group-hover:opacity-10 group-hover:scale-110" />
          </div>
        );
      case "search":
        return (
          <div className="group relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-rose-500/10 to-pink-500/10 border border-rose-500/20 text-rose-500 shadow-soft transition-all duration-300 hover:scale-105 hover:shadow-card">
            <Search className="h-10 w-10 transition-transform duration-300 group-hover:scale-110 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            <div className="absolute -inset-4 rounded-full bg-rose-500 opacity-5 blur-xl pointer-events-none transition-all duration-300 group-hover:opacity-10 group-hover:scale-110" />
          </div>
        );
      default:
        return (
          <div className="group relative flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground transition-all duration-300 hover:scale-105">
            <span className="text-xl transition-transform duration-300 group-hover:scale-110">✨</span>
          </div>
        );
    }
  };

  return (
    <div className={cn("flex flex-col items-center justify-center py-16 px-4 text-center", className)}>
      <div className="mb-4">
        {renderIllustration()}
      </div>
      <h3 className="text-[16px] font-bold text-foreground tracking-tight">{title}</h3>
      {desc && <p className="mt-1.5 max-w-sm text-[13px] text-muted-foreground leading-relaxed">{desc}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}


export function TagChip({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusDot({ online }: { online?: boolean }) {
  return (
    <span
      className={cn(
        "inline-block h-2 w-2 rounded-full ring-2 ring-card",
        online ? "bg-success" : "bg-muted-foreground/40",
      )}
    />
  );
}

export function Avatar({
  src,
  alt,
  size = 32,
  online,
}: {
  src: string;
  alt: string;
  size?: number;
  online?: boolean;
}) {
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <img
        src={src}
        alt={alt}
        width={size}
        height={size}
        className="h-full w-full rounded-full border border-border bg-muted object-cover"
      />
      {online !== undefined && (
        <span className="absolute -bottom-0.5 -right-0.5">
          <StatusDot online={online} />
        </span>
      )}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} />;
}
