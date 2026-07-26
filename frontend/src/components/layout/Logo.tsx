import { APP_LOGO } from "@/lib/logo";
import { useSidebar } from "@/hooks/useSidebar";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export function Logo() {
  const { isCollapsed } = useSidebar();
  
  return (
    <Link to="/dashboard" className="flex items-center gap-3 px-5 py-4 h-[72px]">
      <img src={APP_LOGO} alt="DevLink Logo" className="h-9 w-9 rounded-md shrink-0" />
      <span
        className={cn(
          "text-[18px] font-bold tracking-tight text-foreground whitespace-nowrap transition-all duration-300",
          isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"
        )}
      >
        DevLink
      </span>
    </Link>
  );
}
