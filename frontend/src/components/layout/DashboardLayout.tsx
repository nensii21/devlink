import { Outlet, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { MobileSidebar } from "./MobileSidebar";
import { TopNavbar } from "./TopNavbar";
import { RightPanel } from "./RightPanel";
import { BottomNavigation } from "./BottomNavigation";
import { FAB } from "./FAB";
import { AnnouncementBanner } from "@/components/shared/AnnouncementBanner";
import { SectionErrorBoundary } from "@/components/errors/SectionErrorBoundary";
import { cn } from "@/lib/utils";

export function DashboardLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isDashboard = pathname.endsWith("/dashboard") || pathname === "/";
  const isMessages = pathname.startsWith("/messages");

  return (
    <div
      className={cn(
        "grid h-screen w-full bg-background overflow-hidden grid-cols-1 md:grid-cols-[max-content_1fr]",
        (isDashboard || isMessages) ? "" : "xl:grid-cols-[max-content_1fr_max-content]",
      )}
    >
      {/* ─── Desktop & Tablet Sidebar ─────────────────────────────── */}
      <Sidebar />

      {/* ─── Mobile Slide-out Drawer (secondary / overflow links) ─── */}
      <MobileSidebar />

      {/* ─── Main content column ──────────────────────────────────── */}
      <div className="flex min-w-0 flex-col relative h-screen overflow-hidden">
        <AnnouncementBanner />
        {isMessages ? (
          <div className="hidden md:block">
            <TopNavbar />
          </div>
        ) : (
          <TopNavbar />
        )}

        <main
          // The skip link's destination. tabIndex={-1} makes it focusable so
          // the link can move focus here, not just the scroll position --
          // otherwise the next Tab starts from the top of the document again.
          id="main-content"
          tabIndex={-1}
          className={[
            "flex-1 overflow-y-auto",
            // On mobile add bottom padding so bottom nav never obscures content
            "pb-16 md:pb-0",
            // No focus ring: focus lands here programmatically, and a ring
            // around the whole page reads as a rendering bug.
            "outline-none",
          ].join(" ")}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="mx-auto w-full max-w-7xl px-3 py-4 sm:px-5 lg:px-6"
            >
              <SectionErrorBoundary sectionName="Page View">
                <Outlet />
              </SectionErrorBoundary>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ─── Desktop Right Activity Panel ─────────────────────────── */}
      {!isDashboard && !isMessages && (
        <SectionErrorBoundary sectionName="Right Activity Panel">
          <RightPanel />
        </SectionErrorBoundary>
      )}

      {/* ─── Mobile-only: Bottom Navigation & FAB ─────────────────── */}
      <BottomNavigation />
      {!isMessages && <FAB to="/flares" ariaLabel="Create a new post" />}
    </div>
  );
}
