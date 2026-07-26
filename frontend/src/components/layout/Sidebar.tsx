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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/useSidebar";
import { Logo } from "./Logo";
import { SidebarSection, type SidebarSectionProps } from "./SidebarSection";
import { UserProfile } from "./UserProfile";

export const SIDEBAR_SECTIONS: SidebarSectionProps[] = [
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

export function Sidebar() {
  const { isCollapsed } = useSidebar();

  return (
    <aside
      className={cn(
        "sticky top-0 h-screen hidden lg:flex flex-col border-r border-border bg-sidebar transition-all duration-300",
        isCollapsed ? "w-[80px]" : "w-[280px]"
      )}
    >
      <Logo />
      
      <nav className="flex-1 overflow-y-auto px-2 pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {SIDEBAR_SECTIONS.map((section) => (
          <SidebarSection key={section.label} {...section} />
        ))}
      </nav>

      <UserProfile />
    </aside>
  );
}
