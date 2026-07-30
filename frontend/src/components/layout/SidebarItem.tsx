import { cn } from "@/lib/utils";
import { Link, useRouterState } from "@tanstack/react-router";
import { useSidebar } from "@/hooks/useSidebar";
import type { ReactNode } from "react";

export interface SidebarItemProps {
  label: string;
  to: string;
  icon: ReactNode;
  badge?: number;
  /** When true, renders icon-only regardless of sidebar context state */
  forceCollapsed?: boolean;
}

export function SidebarItem({ label, to, icon, badge, forceCollapsed }: SidebarItemProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { isCollapsed, closeMobile } = useSidebar();

  const collapsed = forceCollapsed ?? isCollapsed;
  const active =
    pathname === to || pathname.startsWith(to.split("?")[0] + "/") || pathname === to.split("?")[0];

  if (collapsed) {
    return (
      <li>
        <Link
          to={to.split("?")[0]}
          onClick={closeMobile}
          title={label}
          aria-label={label}
          aria-current={active ? "page" : undefined}
          className={cn(
            "relative mt-0.5 flex h-11 w-full items-center justify-center rounded-md transition-colors outline-none",
            "focus-visible:ring-2 focus-visible:ring-primary",
            active
              ? "bg-primary-soft text-primary"
              : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground",
          )}
        >
          <span className={cn("shrink-0", active ? "text-primary" : "text-muted-foreground")}>
            {icon}
          </span>
          {/* Badge dot for collapsed state */}
          {badge !== undefined && badge > 0 && (
            <span
              className="absolute right-1.5 top-1.5 flex h-2 w-2 rounded-full bg-destructive"
              aria-hidden="true"
            />
          )}
        </Link>
      </li>
    );
  }

  return (
    <li title={undefined}>
      <Link
        to={to.split("?")[0]}
        preload="intent"
        onClick={closeMobile}
        aria-current={active ? "page" : undefined}
        className={cn(
          "mt-0.5 flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors outline-none",
          "focus-visible:ring-2 focus-visible:ring-primary",
          active
            ? "bg-primary-soft font-semibold text-primary"
            : "text-foreground/80 hover:bg-sidebar-accent hover:text-foreground focus:bg-sidebar-accent",
        )}
      >
        <span className={cn("shrink-0", active ? "text-primary" : "text-muted-foreground")}>
          {icon}
        </span>
        <span className="flex-1 truncate">{label}</span>
        {badge !== undefined && badge > 0 && (
          <span className="rounded-full bg-destructive px-1.5 text-[10px] font-semibold text-destructive-foreground">
            {badge > 9 ? "9+" : badge}
          </span>
        )}
      </Link>
    </li>
  );
}
