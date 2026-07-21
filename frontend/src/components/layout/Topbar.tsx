import { Bell, MessageSquare, Plus, Search, Sparkles, Menu, Moon, Sun } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { currentUser } from "@/mocks/seed";
import { useTheme } from "@/hooks/useTheme";

export function Topbar({
  onMenu,
  onOpenSearch,
}: {
  onMenu: () => void;
  onOpenSearch: () => void;
}) {
  const { isDark, toggleTheme } = useTheme();
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur">
      <button
        onClick={onMenu}
        aria-label="Open menu"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground hover:bg-muted lg:hidden"
      >
        <Menu size={16} />
      </button>

      <button
        type="button"
        onClick={onOpenSearch}
        className="relative flex min-w-0 flex-1 max-w-xl items-center gap-2 rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] text-muted-foreground transition-all hover:border-primary/40 hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
        aria-label="Open global search"
      >
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <span className="truncate">Search developers, projects, skills…</span>
        <kbd className="ml-auto hidden items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground sm:inline-flex">
          ⌘K
        </kbd>
      </button>

      <div className="hidden items-center gap-2 md:flex">
        <button className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-[7px] text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
          <Sparkles size={14} className="text-primary" /> AI Assistant
        </button>
        <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-[7px] text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90">
          <Plus size={14} /> Create
        </button>
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
        <IconButton to="/notifications" count={8}>
          <Bell size={16} />
        </IconButton>
        <IconButton to="/messages" count={3}>
          <MessageSquare size={16} />
        </IconButton>
      </div>

      <Link
        to="/profile/$username"
        params={{ username: currentUser.handle }}
        className="ml-1 flex items-center gap-2 rounded-md p-1 hover:bg-muted"
      >
        <img
          src={currentUser.avatar}
          alt=""
          className="h-8 w-8 rounded-full border border-border bg-muted"
        />
        <div className="hidden text-left sm:block">
          <p className="text-[12px] font-semibold leading-tight text-foreground">
            {currentUser.name}
          </p>
          <p className="text-[11px] leading-tight text-muted-foreground">View Profile</p>
        </div>
      </Link>
    </header>
  );
}

function IconButton({
  children,
  count,
  to,
}: {
  children: React.ReactNode;
  count?: number;
  to: string;
}) {
  return (
    <Link
      to={to}
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
