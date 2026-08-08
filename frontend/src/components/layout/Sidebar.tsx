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
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Logo } from "./Logo";
import { SidebarSection, type SidebarSectionProps } from "./SidebarSection";
import { UserProfile } from "./UserProfile";

export const SIDEBAR_SECTIONS: SidebarSectionProps[] = [
  {
    label: "Navigation",
    items: [
      {
        label: "Dashboard",
        to: "/dashboard",
        icon: <LayoutDashboard size={16} strokeWidth={2} />,
      },
      {
        label: "Projects",
        to: "/projects",
        icon: <FolderKanban size={16} strokeWidth={2} />,
      },
      {
        label: "Explore",
        to: "/search",
        icon: <Compass size={16} strokeWidth={2} />,
      },
      {
        label: "Bookmarks",
        to: "/bookmarks",
        icon: <Bookmark size={16} strokeWidth={2} />,
      },
    ],
  },
  {
    label: "Community",
    items: [
      {
        label: "Builders",
        to: "/builders",
        icon: <Users2 size={16} strokeWidth={2} />,
      },
      {
        label: "Organizations",
        to: "/organizations",
        icon: <Building2 size={16} strokeWidth={2} />,
      },
      {
        label: "AI Matches",
        to: "/builders?tab=matches",
        icon: <Sparkles size={16} strokeWidth={2} />,
      },
      {
        label: "Leaderboard",
        to: "/leaderboard",
        icon: <Trophy size={16} strokeWidth={2} />,
      },
      {
        label: "Connections",
        to: "/builders?tab=connections",
        icon: <Share2 size={16} strokeWidth={2} />,
      },
    ],
  },
  {
    label: "Flares",
    items: [
      {
        label: "Community Feed",
        to: "/flares",
        icon: <Rss size={16} strokeWidth={2} />,
      },
      {
        label: "My Flares",
        to: "/flares?tab=mine",
        icon: <Flame size={16} strokeWidth={2} />,
      },
      {
        label: "Trending",
        to: "/flares?tab=trending",
        icon: <TrendingUp size={16} strokeWidth={2} />,
      },
    ],
  },
  {
    label: "Productivity",
    items: [
      {
        label: "Messages",
        to: "/messages",
        icon: <MessageSquare size={16} strokeWidth={2} />,
        badge: 3,
      },
      {
        label: "Hackathons",
        to: "/hackathons",
        icon: <Trophy size={16} strokeWidth={2} />,
      },
      {
        label: "Notifications",
        to: "/notifications",
        icon: <Bell size={16} strokeWidth={2} />,
        badge: 8,
      },
      {
        label: "Analytics",
        to: "/analytics",
        icon: <BarChart3 size={16} strokeWidth={2} />,
      },
    ],
  },
  {
    label: "Account",
    items: [
      {
        label: "Settings",
        to: "/settings",
        icon: <Settings size={16} strokeWidth={2} />,
      },
    ],
  },
];

export function Sidebar() {
  const { isCollapsed } = useSidebar();
  // On tablet (md–xl) always force icon-only regardless of toggle state
  const isTablet = useMediaQuery("(min-width: 768px) and (max-width: 1279px)");
  const collapsed = isTablet || isCollapsed;

  return (
    <aside
      aria-expanded={!collapsed}
      className={cn(
        // Hidden on mobile; visible from md up
        "h-screen hidden md:flex flex-col border-r border-border bg-sidebar transition-all duration-300",
        // Tablet: narrow icon rail; Desktop: full or collapsed width
        collapsed ? "w-[72px]" : "w-[280px]",
      )}
    >
      <Logo />

      <nav
        className="flex-1 overflow-y-auto px-2 pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
        aria-label="Sidebar navigation"
      >
        {SIDEBAR_SECTIONS.map((section) => (
          <SidebarSection key={section.label} {...section} forceCollapsed={collapsed} />
        ))}
      </nav>

      <UserProfile forceCollapsed={collapsed} />
    </aside>
  );
}
