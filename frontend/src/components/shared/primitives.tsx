import { cn, getInitials } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { useCardAnimation } from "@/lib/animations";

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

export function AnimatedCard({
  children,
  className,
  interactive = false,
  index = 0,
}: {
  children?: ReactNode;
  className?: string;
  interactive?: boolean;
  index?: number;
}) {
  const animation = useCardAnimation(index);

  return (
    <motion.div
      variants={animation.variants}
      initial={animation.initial}
      animate={animation.animate}
      custom={animation.custom}
      whileHover={animation.whileHover}
    >
      <Card interactive={interactive} className={cn("will-change-transform", className)}>
        {children}
      </Card>
    </motion.div>
  );
}

export function EmptyState({
  title,
  desc,
  action,
}: {
  title: string;
  desc?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-3 grid h-12 w-12 place-items-center rounded-full bg-muted text-muted-foreground">
        ✨
      </div>
      <p className="text-[14px] font-semibold text-foreground">{title}</p>
      {desc && <p className="mt-1 max-w-xs text-[13px] text-muted-foreground">{desc}</p>}
      {action && <div className="mt-4">{action}</div>}
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
  name,
}: {
  src?: string | null;
  alt: string;
  size?: number;
  online?: boolean;
  name?: string | null;
}) {
  const [hasError, setHasError] = useState(false);
  const normalizedSrc = typeof src === "string" ? src.trim() : "";
  const shouldRenderImage = Boolean(normalizedSrc) && !hasError;
  const fallbackLabel = alt || name || "User avatar";

  useEffect(() => {
    setHasError(false);
  }, [normalizedSrc]);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      {shouldRenderImage ? (
        <img
          src={normalizedSrc}
          alt={alt}
          width={size}
          height={size}
          onError={() => setHasError(true)}
          className="h-full w-full rounded-full border border-border bg-muted object-cover"
        />
      ) : (
        <div
          aria-label={fallbackLabel}
          className="flex h-full w-full items-center justify-center rounded-full border border-border bg-primary/10 text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-primary"
        >
          {getInitials(name ?? alt)}
        </div>
      )}
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
