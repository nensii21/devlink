import { AnimatePresence, motion } from "framer-motion";
import { useSidebar } from "@/hooks/useSidebar";
import { SIDEBAR_SECTIONS } from "./Sidebar";
import { SidebarSection } from "./SidebarSection";
import { UserProfile } from "./UserProfile";
import { Logo } from "./Logo";

export function MobileSidebar() {
  const { isMobileOpen, closeMobile } = useSidebar();

  return (
    <AnimatePresence>
      {isMobileOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={closeMobile}
          />
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", bounce: 0, duration: 0.3 }}
            className="fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-border bg-sidebar shadow-lg lg:hidden"
          >
            <div className="flex items-center justify-between px-2">
              <Logo />
            </div>

            <nav className="flex-1 overflow-y-auto px-2 pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {SIDEBAR_SECTIONS.map((section) => (
                <SidebarSection key={section.label} {...section} />
              ))}
            </nav>

            <UserProfile />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
