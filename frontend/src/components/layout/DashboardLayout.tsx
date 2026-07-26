import { Outlet, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { MobileSidebar } from "./MobileSidebar";
import { TopNavbar } from "./TopNavbar";
import { RightPanel } from "./RightPanel";

export function DashboardLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  
  return (
    <div className="flex min-h-screen w-full bg-background overflow-hidden">
      <Sidebar />
      <MobileSidebar />
      
      <div className="flex min-w-0 flex-1 flex-col relative h-screen">
        <TopNavbar />
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              className="mx-auto w-full max-w-[1400px] px-4 py-6 sm:px-6"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      
      <RightPanel />
    </div>
  );
}
