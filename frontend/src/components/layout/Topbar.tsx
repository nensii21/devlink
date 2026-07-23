import { Bell, MessageSquare, Plus, Search, Sparkles, Menu, Moon, Sun } from "lucide-react";
import { Link, useNavigate } from "@tanstack/react-router";
import { currentUser, builders, projects, flares } from "@/mocks/seed";
import { useTheme } from "@/hooks/useTheme";
import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

// Extract unique skills for autocomplete predictions
const skillSetMap = new Map<string, string>();
[
  ...builders.flatMap((b) => b.skills),
  ...projects.flatMap((p) => p.stack),
  ...flares.flatMap((f) => f.tags),
].forEach((skill) => {
  const normalized = skill.toLowerCase();
  if (!skillSetMap.has(normalized) || skill[0] === skill[0].toUpperCase()) {
    skillSetMap.set(normalized, skill);
  }
});
const ALL_SKILLS = Array.from(skillSetMap.values()).sort((a, b) => a.localeCompare(b));

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  // Click outside detection to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const suggestions = inputValue.trim()
    ? ALL_SKILLS.filter((skill) => skill.toLowerCase().includes(inputValue.toLowerCase())).slice(
        0,
        6,
      )
    : [];

  useEffect(() => {
    setHighlightedIndex(-1);
  }, [inputValue]);

  const selectSkill = (skill: string) => {
    setInputValue("");
    setIsFocused(false);
    navigate({
      to: "/search",
      search: { q: skill },
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (suggestions.length === 0) {
      if (e.key === "Enter") {
        e.preventDefault();
        selectSkill(inputValue);
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
        selectSkill(suggestions[highlightedIndex]);
      } else {
        selectSkill(inputValue);
      }
    } else if (e.key === "Escape") {
      setIsFocused(false);
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur">
      <button
        onClick={onMenu}
        aria-label="Open menu"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground hover:bg-muted lg:hidden"
      >
        <Menu size={16} />
      </button>

      <div ref={containerRef} className="relative min-w-0 flex-1 max-w-xl">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          type="search"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search DevLink…"
          className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] text-foreground placeholder:text-muted-foreground outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
        />

        {isFocused && suggestions.length > 0 && (
          <div className="absolute left-0 right-0 top-full z-30 mt-1.5 overflow-hidden rounded-md border border-border bg-surface shadow-lg backdrop-blur-sm">
            <div className="p-1">
              <p className="px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/75">
                Suggested Skills
              </p>
              {suggestions.map((s, index) => (
                <button
                  key={s}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    selectSkill(s);
                  }}
                  className={cn(
                    "flex w-full items-center rounded-sm px-2.5 py-1.5 text-left text-[13px] transition-colors cursor-pointer",
                    index === highlightedIndex
                      ? "bg-primary text-primary-foreground font-medium"
                      : "text-foreground hover:bg-muted/70",
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

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
