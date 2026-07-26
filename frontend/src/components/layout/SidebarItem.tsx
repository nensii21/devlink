import { cn } from "@/lib/utils";
import { Link, useRouterState } from "@tanstack/react-router";
import { useSidebar } from "@/hooks/useSidebar";
import type { ReactNode } from "react";

export interface SidebarItemProps {
  label: string;
  to: string;
  icon: ReactNode;
  badge?: number;
}

export function SidebarItem({ label, to, icon, badge }: SidebarItemProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { isCollapsed, closeMobile } = useSidebar();
  
  const active = pathname === to || pathname.startsWith(to.split("?")[0] + "/");

  return (
    <li title={isCollapsed ? label : undefined}>
      <Link
        to={to.split("?")[0]}
        onClick={closeMobile}
        className={cn(
          "mt-1 flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary",
          active
            ? "bg-primary-soft font-semibold text-primary"
            : "text-foreground/80 hover:bg-sidebar-accent hover:text-foreground focus:bg-sidebar-accent",
          isCollapsed ? "justify-center px-0 mx-2" : ""
        )}
      >
        <span className={cn("shrink-0", active ? "text-primary" : "text-muted-foreground")}>
          {icon}
        </span>
        {!isCollapsed && (
          <>
            <span className="flex-1 truncate">{label}</span>
            {badge !== undefined && (
              <span className="rounded-full bg-destructive px-1.5 text-[10px] font-semibold text-destructive-foreground">
                {badge}
              </span>
            )}
          </>
        )}
        {/* For collapsed state badge indication */}
        {isCollapsed && badge !== undefined && (
          <span className="absolute top-1 right-1 flex h-2 w-2 rounded-full bg-destructive"></span>
        )}
      </Link>
    </li>
  );
}
