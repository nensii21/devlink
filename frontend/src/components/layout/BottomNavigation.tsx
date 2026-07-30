import { Link, useRouterState } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { LayoutDashboard, Users2, MessageSquare, Bell } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  to: string;
  icon: React.ElementType;
  badge?: number;
  ariaLabel: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Home",
    to: "/dashboard",
    icon: LayoutDashboard,
    ariaLabel: "Go to Dashboard",
  },
  {
    label: "Builders",
    to: "/builders",
    icon: Users2,
    ariaLabel: "Explore Builders",
  },
  {
    label: "Messages",
    to: "/messages",
    icon: MessageSquare,
    badge: 3,
    ariaLabel: "Messages (3 unread)",
  },
  {
    label: "Alerts",
    to: "/notifications",
    icon: Bell,
    badge: 8,
    ariaLabel: "Notifications (8 new)",
  },
];

export function BottomNavigation() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <nav
      aria-label="Mobile navigation"
      className={cn(
        "md:hidden",
        "fixed bottom-0 left-0 right-0 z-50",
        "flex h-16 items-stretch justify-around",
        "border-t border-border bg-background/95 backdrop-blur-sm",
        // Safe area inset for devices with home indicators
        "pb-safe",
      )}
    >
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.to || pathname.startsWith(item.to + "/");
        const Icon = item.icon;

        return (
          <Link
            key={item.label}
            to={item.to}
            aria-label={item.ariaLabel}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              // Touch target: at least 44×44px
              "relative flex flex-1 flex-col items-center justify-center gap-0.5 min-h-[44px]",
              "transition-colors duration-150 outline-none",
              "focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset",
              isActive ? "text-primary" : "text-muted-foreground",
            )}
          >
            {/* Active background pill */}
            {isActive && (
              <motion.span
                layoutId="bottom-nav-active"
                className="absolute inset-x-3 inset-y-1.5 rounded-xl bg-primary/10"
                transition={{ type: "spring", stiffness: 380, damping: 34 }}
              />
            )}

            {/* Icon + Badge */}
            <span className="relative z-10">
              <Icon
                size={22}
                strokeWidth={isActive ? 2.25 : 1.75}
                className={cn("transition-transform duration-200", isActive && "scale-110")}
              />
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className="absolute -right-1.5 -top-1.5 grid h-4 min-w-[16px] place-items-center rounded-full bg-destructive px-1 text-[9px] font-bold text-destructive-foreground"
                  aria-hidden="true"
                >
                  {item.badge > 9 ? "9+" : item.badge}
                </span>
              )}
            </span>

            {/* Label */}
            <span
              className={cn(
                "relative z-10 text-[10px] font-medium tracking-wide leading-none transition-colors",
                isActive ? "text-primary" : "text-muted-foreground",
              )}
            >
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
