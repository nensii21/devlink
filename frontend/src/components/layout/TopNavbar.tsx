import {
  MessageSquare,
  Plus,
  Sparkles,
  Menu,
  Moon,
  Sun,
  PanelLeftClose,
  PanelLeftOpen,
  BadgeCheck,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useSidebar } from "@/hooks/useSidebar";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/ui/search-bar";
import { cn } from "@/lib/utils";

import { currentUser } from "@/mocks/seed";
import { useTheme } from "@/hooks/useTheme";
import { NotificationCenter } from "@/components/shared/NotificationCenter";
import { useState, useEffect } from "react";
import { GlobalSearchModal } from "@/components/search/GlobalSearchModal";
import { toast } from "sonner";
import { TypoCaption } from "@/components/shared/Typography";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

import { WorkspaceStatusIndicator } from "./WorkspaceStatusIndicator";

export function TopNavbar() {
  const { isDark, toggleTheme } = useTheme();
  const { toggleMobile, toggleSidebar, isCollapsed } = useSidebar();
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Global Cmd+K / Ctrl+K hotkey
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-20 flex h-[72px] items-center gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur">
        {/* Hamburger: visible on tablet only (md to lg). Mobile uses BottomNavigation instead. */}
        <button
          onClick={toggleMobile}
          aria-label="Open navigation menu"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground hover:bg-muted md:grid lg:hidden hidden transition-colors"
        >
          <Menu size={16} />
        </button>

        <button
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          className="hidden lg:grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground hover:bg-muted transition-colors"
        >
          {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>

        <div className="relative min-w-0 flex-1 max-w-xl">
          <SearchBar
            isButton
            onTriggerClick={() => setIsSearchOpen(true)}
            placeholder="Search developers, projects, posts, messages, hackathons, repos..."
            shortcut="⌘K"
          />
        </div>

        {/* Global Workspace Status Indicator in Navbar */}
        <div className="hidden sm:flex items-center">
          <WorkspaceStatusIndicator />
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <Sparkles size={14} className="text-primary" /> AI Assistant
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="primary" size="sm" className="gap-1.5 text-xs font-semibold">
                <Plus size={14} /> Create
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[180px]">
              <DropdownMenuItem asChild>
                <Link to="/projects" search={{ create: true }}>
                  New Project
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/flares">New Flare</Link>
              </DropdownMenuItem>
              <DropdownMenuItem
                onSelect={() => {
                  navigator.clipboard.writeText("https://devlink.com/invite/builder");
                  toast.success("Invitation link copied to clipboard!");
                }}
                className="cursor-pointer"
              >
                Invite Builder
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/organizations">Organization</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to="/hackathons" search={{ create: true }}>
                  Hackathon
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <NotificationCenter />
          <IconButton to="/messages" count={3} ariaLabel="Messages, 3 unread">
            <MessageSquare size={16} />
          </IconButton>
        </div>

        <Link
          to="/profile/$username"
          params={{ username: currentUser.handle }}
          className="ml-1 flex items-center gap-2 rounded-md p-1 hover:bg-muted transition-colors"
        >
          <Avatar
            src={currentUser.avatar}
            alt={currentUser.name}
            name={currentUser.name}
            size="sm"
          />
          <div className="hidden text-left sm:block">
            <p className="text-[12px] font-semibold leading-tight text-foreground flex items-center gap-1">
              {currentUser.name}
              {currentUser.verified && (
                <BadgeCheck
                  className={cn(
                    "h-3 w-3 shrink-0",
                    currentUser.premium
                      ? "text-amber-500 fill-amber-500/10 animate-pulse"
                      : "text-primary",
                  )}
                  aria-label={currentUser.premium ? "Premium Verified User" : "Verified User"}
                />
              )}
            </p>
            <TypoCaption as="p">View Profile</TypoCaption>
          </div>
        </Link>
      </header>
      <GlobalSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  );
}

function IconButton({
  children,
  count,
  to,
  ariaLabel,
}: {
  children: React.ReactNode;
  count?: number;
  to: string;
  ariaLabel: string;
}) {
  return (
    <Link
      to={to}
      aria-label={ariaLabel}
      className="relative grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-[16px] place-items-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground">
          {count}
        </span>
      )}
    </Link>
  );
}
