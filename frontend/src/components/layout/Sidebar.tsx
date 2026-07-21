import { cn } from "@/lib/utils";
import { Link, useRouterState } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import {
  LayoutDashboard,
  FolderKanban,
  Compass,
  Bookmark,
  Users2,
  Building2,
  Sparkles,
  Share2,
  Flame,
  Rss,
  TrendingUp,
  MessageSquare,
  Trophy,
  Bell,
  BarChart3,
  Settings,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { currentUser } from "@/mocks/seed";

type Item = { label: string; to: string; icon: ReactNode; badge?: number };
type Group = { label: string; items: Item[] };

const groups: Group[] = [
  {
    label: "Navigation",
    items: [
      { label: "Dashboard", to: "/dashboard", icon: <LayoutDashboard size={16} /> },
      { label: "Projects", to: "/projects", icon: <FolderKanban size={16} /> },
      { label: "Explore", to: "/search", icon: <Compass size={16} /> },
      { label: "Bookmarks", to: "/bookmarks", icon: <Bookmark size={16} /> },
    ],
  },
  {
    label: "Community",
    items: [
      { label: "Builders", to: "/builders", icon: <Users2 size={16} /> },
      { label: "Organizations", to: "/organizations", icon: <Building2 size={16} /> },
      { label: "AI Matches", to: "/builders?tab=matches", icon: <Sparkles size={16} /> },
      { label: "Connections", to: "/builders?tab=connections", icon: <Share2 size={16} /> },
    ],
  },
  {
    label: "Flares",
    items: [
      { label: "Community Feed", to: "/flares", icon: <Rss size={16} /> },
      { label: "My Flares", to: "/flares?tab=mine", icon: <Flame size={16} /> },
      { label: "Trending", to: "/flares?tab=trending", icon: <TrendingUp size={16} /> },
    ],
  },
  {
    label: "Productivity",
    items: [
      { label: "Messages", to: "/messages", icon: <MessageSquare size={16} />, badge: 3 },
      { label: "Hackathons", to: "/hackathons", icon: <Trophy size={16} /> },
      { label: "Notifications", to: "/notifications", icon: <Bell size={16} />, badge: 8 },
      { label: "Analytics", to: "/analytics", icon: <BarChart3 size={16} /> },
    ],
  },
  {
    label: "Account",
    items: [{ label: "Settings", to: "/settings", icon: <Settings size={16} /> }],
  },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {open && (
          <motion.button
            aria-label="Close menu"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-30 bg-foreground/20 lg:hidden"
          />
        )}
      </AnimatePresence>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-sidebar transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <Link to="/dashboard" className="flex items-center gap-2 px-5 py-4">
          <img src={APP_LOGO} alt="" className="h-8 w-8 rounded-md" />
          <span className="text-[18px] font-bold tracking-tight text-foreground">DevLink</span>
        </Link>

        <nav className="flex-1 overflow-y-auto px-3 pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {groups.map((group) => (
            <SidebarGroup key={group.label} group={group} onNav={onClose} />
          ))}
        </nav>

        <div className="border-t border-sidebar-border px-3 py-3">
          <Link
            to="/profile/$username"
            params={{ username: currentUser.handle }}
            onClick={onClose}
            className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-sidebar-accent"
          >
            <img
              src={currentUser.avatar}
              alt=""
              className="h-9 w-9 rounded-full border border-border bg-muted"
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-foreground">
                {currentUser.name}
              </p>
              <p className="truncate text-[12px] text-muted-foreground">@{currentUser.handle}</p>
            </div>
            {currentUser.premium && (
              <span className="rounded-md bg-primary-soft px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                PRO
              </span>
            )}
          </Link>
          <button className="mt-1 flex w-full items-center gap-3 rounded-md px-2 py-2 text-[13px] text-muted-foreground hover:bg-sidebar-accent hover:text-foreground">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>
    </>
  );
}

function SidebarGroup({ group, onNav }: { group: Group; onNav: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [open, setOpen] = useState(true);
  return (
    <div className="mt-4 first:mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground"
      >
        {group.label}
        <ChevronRight size={12} className={cn("transition-transform", open && "rotate-90")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            {group.items.map((item) => {
              const active =
                pathname === item.to || pathname.startsWith(item.to.split("?")[0] + "/");
              return (
                <li key={item.label}>
                  <Link
                    to={item.to.split("?")[0]}
                    onClick={onNav}
                    className={cn(
                      "mt-0.5 flex items-center gap-2.5 rounded-md px-2 py-2 text-[13px] font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      active
                        ? "bg-primary-soft font-semibold text-primary"
                        : "text-foreground/80 hover:bg-sidebar-accent hover:text-foreground focus:bg-sidebar-accent",
                    )}
                  >
                    <span className={cn(active ? "text-primary" : "text-muted-foreground")}>
                      {item.icon}
                    </span>
                    <span className="flex-1 truncate">{item.label}</span>
                    {item.badge !== undefined && (
                      <span className="rounded-full bg-destructive px-1.5 text-[10px] font-semibold text-destructive-foreground">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
