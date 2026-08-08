import { Link } from "@tanstack/react-router";
import { LogOut, BadgeCheck } from "lucide-react";
import { Avatar } from "@/components/shared/primitives";
import { cn } from "@/lib/utils";
import { currentUser } from "@/mocks/seed";
import { useSidebar } from "@/hooks/useSidebar";

interface UserProfileProps {
  /** When true, renders compact avatar-only view regardless of sidebar state */
  forceCollapsed?: boolean;
}

export function UserProfile({ forceCollapsed }: UserProfileProps) {
  const { isCollapsed, closeMobile } = useSidebar();
  const collapsed = forceCollapsed ?? isCollapsed;

  if (collapsed) {
    return (
      <div className="border-t border-sidebar-border px-2 py-3 flex flex-col items-center gap-3">
        <Link
          to="/profile/$username"
          params={{ username: currentUser.handle }}
          onClick={closeMobile}
          className="rounded-full transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          title={currentUser.name}
          aria-label={`View ${currentUser.name}'s profile`}
        >
          <Avatar
            src={currentUser.avatar}
            alt={currentUser.name}
            name={currentUser.name}
            size={36}
          />
        </Link>
        <button
          title="Logout"
          aria-label="Logout"
          className="text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-md p-1"
        >
          <LogOut size={18} />
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-sidebar-border px-3 py-3">
      <Link
        to="/profile/$username"
        params={{ username: currentUser.handle }}
        onClick={closeMobile}
        className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-sidebar-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <Avatar src={currentUser.avatar} alt={currentUser.name} name={currentUser.name} size={36} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold text-foreground flex items-center gap-1">
            {currentUser.name}
            {currentUser.verified && (
              <BadgeCheck
                className={cn(
                  "h-3.5 w-3.5 shrink-0",
                  currentUser.premium ? "text-amber-500 fill-amber-500/10 animate-pulse" : "text-primary"
                )}
                aria-label={currentUser.premium ? "Premium Verified User" : "Verified User"}
              />
            )}
          </p>
          <p className="truncate text-[12px] text-muted-foreground">@{currentUser.handle}</p>
        </div>
        {currentUser.premium && (
          <span className="rounded-md bg-amber-500/15 border border-amber-500/30 px-1.5 py-0.5 text-[10px] font-semibold text-amber-500 animate-pulse">
            PRO
          </span>
        )}
      </Link>
      <button className="mt-1 flex w-full items-center gap-3 rounded-md px-2 py-2 text-[13px] text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary">
        <LogOut size={16} /> Logout
      </button>
    </div>
  );
}
