import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/useSidebar";
import { SidebarItem, type SidebarItemProps } from "./SidebarItem";

export interface SidebarSectionProps {
  label: string;
  items: SidebarItemProps[];
}

export function SidebarSection({ label, items }: SidebarSectionProps) {
  const [open, setOpen] = useState(true);
  const { isCollapsed } = useSidebar();

  if (isCollapsed) {
    return (
      <div className="mt-4 first:mt-2 relative">
        <ul className="space-y-1">
          {items.map((item) => (
            <SidebarItem key={item.label} {...item} />
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className="mt-4 first:mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground"
      >
        {label}
        <ChevronRight size={12} className={cn("transition-transform duration-200", open && "rotate-90")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
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
