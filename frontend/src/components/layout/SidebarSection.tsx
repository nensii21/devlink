import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/useSidebar";
import { SidebarItem, type SidebarItemProps } from "./SidebarItem";

export interface SidebarSectionProps {
  label: string;
  items: SidebarItemProps[];
  /** When true, renders icon-only regardless of sidebar context state */
  forceCollapsed?: boolean;
}

function getStoredOpenState(label: string): boolean {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem(`sidebar-section-open:${label}`);
  return stored === null ? true : stored === "true";
}

export function SidebarSection({ label, items, forceCollapsed }: SidebarSectionProps) {
  const [open, setOpen] = useState(() => getStoredOpenState(label));
  const { isCollapsed } = useSidebar();
  const collapsed = forceCollapsed ?? isCollapsed;
  const prefersReducedMotion = useReducedMotion();

  const toggle = () => {
    setOpen((v) => {
      const next = !v;
      if (typeof window !== "undefined") {
        localStorage.setItem(`sidebar-section-open:${label}`, String(next));
      }
      return next;
    });
  };

  if (collapsed) {
    return (
      <div className="mt-3 first:mt-2 relative">
        {/* Tiny divider between sections when collapsed */}
        <span className="block mx-3 mb-2 h-px bg-border/60" aria-hidden="true" />
        <ul className="space-y-0.5">
          {items.map((item) => (
            <SidebarItem key={item.label} {...item} forceCollapsed />
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="mt-3 first:mt-2">
      <button
        onClick={toggle}
        className="flex w-full items-center justify-between rounded-md px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground transition-colors duration-150 hover:bg-sidebar-accent/60 hover:text-foreground"
        aria-expanded={open}
      >
        {label}
        <ChevronRight
          size={12}
          className={cn("transition-transform duration-200", open && "rotate-90")}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.ul
            initial={prefersReducedMotion ? undefined : { height: 0, opacity: 0 }}
            animate={prefersReducedMotion ? undefined : { height: "auto", opacity: 1 }}
            exit={prefersReducedMotion ? undefined : { height: 0, opacity: 0 }}
            className="overflow-hidden space-y-0.5"
          >
            {items.map((item) => (
              <SidebarItem key={item.label} {...item} />
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
