import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { Link } from "@tanstack/react-router";

interface FABProps {
  /** Route to navigate to. Defaults to /flares (create post) */
  to?: string;
  /** Screen-reader label */
  ariaLabel?: string;
  /** Custom click handler — if provided, no navigation occurs */
  onClick?: () => void;
}

/**
 * Floating Action Button — visible on mobile only (< md).
 * Sits above the BottomNavigation (bottom-20).
 */
export function FAB({ to = "/flares", ariaLabel = "Create a new post", onClick }: FABProps) {
  const baseClasses = [
    // Layout
    "md:hidden fixed bottom-[76px] right-4 z-50",
    "flex h-14 w-14 items-center justify-center",
    // Shape & color
    "rounded-full bg-primary text-primary-foreground",
    // Shadow
    "shadow-[0_4px_16px_rgba(5,183,215,0.45)]",
    // Interactions
    "transition-transform duration-200 ease-out",
    "hover:scale-110 active:scale-95",
    // Accessibility
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
  ].join(" ");

  const content = (
    <motion.span
      initial={{ rotate: 0 }}
      whileHover={{ rotate: 90 }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
      className="flex items-center justify-center"
    >
      <Plus size={26} strokeWidth={2.5} />
    </motion.span>
  );

  if (onClick) {
    return (
      <button type="button" aria-label={ariaLabel} onClick={onClick} className={baseClasses}>
        {content}
      </button>
    );
  }

  return (
    <Link to={to} aria-label={ariaLabel} className={baseClasses}>
      {content}
    </Link>
  );
}
