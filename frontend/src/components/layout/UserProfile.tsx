import { Link } from "@tanstack/react-router";
import { LogOut } from "lucide-react";
import { Avatar } from "@/components/shared/primitives";
import { currentUser } from "@/mocks/seed";
import { useSidebar } from "@/hooks/useSidebar";

export function UserProfile() {
  const { isCollapsed, closeMobile } = useSidebar();

  if (isCollapsed) {
    return (
      <div className="border-t border-sidebar-border px-2 py-3 flex flex-col items-center gap-4">
        <Link
          to="/profile/$username"
          params={{ username: currentUser.handle }}
          onClick={closeMobile}
          className="rounded-full transition-transform hover:scale-105"
          title="Profile"
        >
          <Avatar src={currentUser.avatar} alt={currentUser.name} name={currentUser.name} size={36} />
        </Link>
        <button title="Logout" className="text-muted-foreground hover:text-foreground">
          <LogOut size={20} />
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
        className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-sidebar-accent transition-colors"
      >
        <Avatar src={currentUser.avatar} alt={currentUser.name} name={currentUser.name} size={36} />
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
      <button className="mt-1 flex w-full items-center gap-3 rounded-md px-2 py-2 text-[13px] text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition-colors">
        <LogOut size={16} /> Logout
      </button>
    </div>
  );
}
