import { cn, getInitials } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { useEffect, useState, type ReactNode, type ComponentType } from "react";
import { motion } from "framer-motion";
import { useCardAnimation } from "@/lib/animations";
import { FolderKanban, BellOff, MessageSquareDashed, UserX, SearchX, Sparkles } from "lucide-react";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

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
    <div className={cn("flex items-center justify-between px-5 pt-4 pb-3.5", className)}>
      <TypoSection>
        <span className="inline-block h-2 w-2 rounded-full bg-primary/80" />
        {title}
      </TypoSection>
      {action &&
        (actionTo ? (
          <Link
            to={actionTo}
            className="text-[12px] font-semibold text-primary transition-all hover:text-primary/80 hover:underline"
          >
            {action}
          </Link>
        ) : (
          <button className="text-[12px] font-semibold text-primary transition-all hover:text-primary/80 hover:underline">
            {action}
          </button>
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
        "rounded-2xl border border-border/70 bg-card shadow-xs transition-all duration-200",
        interactive && "hover-lift hover:border-primary/40 hover:shadow-card",
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
  icon: Icon = Sparkles,
  title,
  desc,
  action,
  className,
  illustration,
}: {
  icon?: ComponentType<{ className?: string; size?: number }> | ReactNode;
  title: string;
  desc?: string;
  action?: ReactNode;
  className?: string;
  illustration?:
    | "empty-box"
    | "no-results"
    | "no-messages"
    | "no-notifications"
    | "no-bookmarks"
    | "no-projects";
}) {
  const isComponent =
    typeof Icon === "function" ||
    (typeof Icon === "object" && Icon !== null && "render" in (Icon as object));
  const IconComp = isComponent
    ? (Icon as ComponentType<{ className?: string; size?: number }>)
    : null;

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4 text-center animate-in fade-in duration-200",
        className,
      )}
    >
      <div className="mb-4">
        {illustration ? (
          <EmptyIllustration variant={illustration} />
        ) : (
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-primary-soft text-primary shadow-xs">
            {IconComp ? <IconComp size={24} /> : ((Icon as ReactNode) ?? "\u2728")}
          </div>
        )}
      </div>
      <TypoSection>{title}</TypoSection>
      {desc && (
        <TypoCaption as="p">{desc}</TypoCaption>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function NoProjectsEmptyState({
  title = "No projects found",
  desc = "There are no projects available right now. Create a new project to start collaborating!",
  action,
}: {
  title?: string;
  desc?: string;
  action?: ReactNode;
}) {
  return <EmptyState title={title} desc={desc} action={action} illustration="no-projects" />;
}

export function NoNotificationsEmptyState({
  title = "No notifications yet",
  desc = "You're all caught up! Updates and notifications will appear here as they arrive.",
}: {
  title?: string;
  desc?: string;
}) {
  return <EmptyState title={title} desc={desc} illustration="no-notifications" />;
}

export function NoMessagesEmptyState({
  title = "No messages",
  desc = "Your inbox is empty. Connect with other developers or start a conversation from a profile.",
  action,
}: {
  title?: string;
  desc?: string;
  action?: ReactNode;
}) {
  return <EmptyState title={title} desc={desc} action={action} illustration="no-messages" />;
}

export function NoConnectionsEmptyState({
  title = "No connections found",
  desc = "We couldn't find any developers matching your filter criteria.",
  action,
}: {
  title?: string;
  desc?: string;
  action?: ReactNode;
}) {
  return <EmptyState icon={UserX} title={title} desc={desc} action={action} />;
}

export function NoSearchResultsEmptyState({
  title = "No results found",
  desc = "No matching items found for your search query. Try searching with different keywords.",
  action,
}: {
  title?: string;
  desc?: string;
  action?: ReactNode;
}) {
  return <EmptyState title={title} desc={desc} action={action} illustration="no-results" />;
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
          <rect
            x="30"
            y="30"
            width="60"
            height="50"
            rx="6"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.3"
          />
          <rect
            x="40"
            y="40"
            width="40"
            height="30"
            rx="4"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.4"
          />
          <line
            x1="50"
            y1="50"
            x2="70"
            y2="50"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.3"
            strokeLinecap="round"
          />
          <line
            x1="50"
            y1="58"
            x2="65"
            y2="58"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.2"
            strokeLinecap="round"
          />
          <circle cx="35" cy="25" r="3" fill="var(--primary)" opacity="0.2" />
          <circle cx="85" cy="22" r="2" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-results" && (
        <>
          <circle
            cx="50"
            cy="45"
            r="25"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.25"
          />
          <line
            x1="68"
            y1="63"
            x2="80"
            y2="75"
            stroke="var(--muted-foreground)"
            strokeWidth="3"
            opacity="0.2"
            strokeLinecap="round"
          />
          <line
            x1="42"
            y1="42"
            x2="58"
            y2="42"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.3"
            strokeLinecap="round"
          />
          <line
            x1="42"
            y1="50"
            x2="54"
            y2="50"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.2"
            strokeLinecap="round"
          />
          <circle cx="35" cy="25" r="3" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-messages" && (
        <>
          <rect
            x="25"
            y="25"
            width="70"
            height="40"
            rx="8"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.25"
          />
          <path
            d="M40 35 L55 35 M40 45 L65 45 M40 55 L50 55"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.3"
            strokeLinecap="round"
          />
          <circle cx="35" cy="20" r="2" fill="var(--primary)" opacity="0.15" />
          <circle cx="88" cy="22" r="2.5" fill="var(--primary)" opacity="0.2" />
        </>
      )}
      {variant === "no-notifications" && (
        <>
          <path
            d="M50 25 C42 25 38 30 38 38 L38 55 L32 55 L68 55 L62 55 L62 38 C62 30 58 25 50 25"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.25"
            strokeLinejoin="round"
          />
          <circle cx="50" cy="68" r="4" stroke="var(--primary)" strokeWidth="2" opacity="0.3" />
          <circle cx="35" cy="22" r="2" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-bookmarks" && (
        <>
          <path
            d="M35 25 L35 70 L50 58 L65 70 L65 25 Z"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.25"
            strokeLinejoin="round"
          />
          <line
            x1="42"
            y1="35"
            x2="58"
            y2="35"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.2"
            strokeLinecap="round"
          />
          <circle cx="30" cy="22" r="2.5" fill="var(--primary)" opacity="0.15" />
        </>
      )}
      {variant === "no-projects" && (
        <>
          <rect
            x="30"
            y="25"
            width="25"
            height="25"
            rx="4"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.25"
          />
          <rect
            x="65"
            y="30"
            width="25"
            height="25"
            rx="4"
            stroke="var(--primary)"
            strokeWidth="2"
            opacity="0.3"
          />
          <rect
            x="45"
            y="60"
            width="25"
            height="25"
            rx="4"
            stroke="var(--muted-foreground)"
            strokeWidth="2"
            opacity="0.2"
          />
          <circle cx="35" cy="20" r="2" fill="var(--primary)" opacity="0.15" />
          <circle cx="90" cy="22" r="2" fill="var(--primary)" opacity="0.1" />
        </>
      )}
    </svg>
  );
}
export function TagChip({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-border/60 bg-muted/80 px-2 py-0.5 text-[11px] font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary-soft/40 hover:text-primary",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusDot({ online }: { online?: boolean }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {online && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
      )}
      <span
        className={cn(
          "relative inline-flex h-2.5 w-2.5 rounded-full ring-2 ring-card",
          online ? "bg-success" : "bg-muted-foreground/40",
        )}
      />
    </span>
  );
}

export function Avatar({
  src,
  alt,
  size = 32,
  online,
  name,
  className,
}: {
  src?: string | null;
  alt: string;
  size?: number;
  online?: boolean;
  name?: string | null;
  className?: string;
}) {
  const [hasError, setHasError] = useState(false);
  const normalizedSrc = typeof src === "string" ? src.trim() : "";
  const shouldRenderImage = Boolean(normalizedSrc) && !hasError;
  const fallbackLabel = alt || name || "User avatar";

  useEffect(() => {
    setHasError(false);
  }, [normalizedSrc]);

  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }}>
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

// export function NoNotificationsEmptyState() {
//   return (
//     <EmptyState
//       title="No notifications"
//       desc="You're all caught up! Check back later for new updates."
//     />
//   );
// }

// export function NoMessagesEmptyState({
//   title = "No messages",
//   desc = "You don't have any messages yet.",
// }: {
//   title?: string;
//   desc?: string;
// }) {
//   return <EmptyState title={title} desc={desc} />;
// }

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-xl bg-muted/70", className)} />;
}
