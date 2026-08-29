import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import {
  Search,
  X,
  Users,
  FolderGit2,
  Rss,
  MessageSquare,
  Trophy,
  GitBranch,
  Clock,
  Trash2,
  CornerDownLeft,
  Command,
  LayoutDashboard,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useDebounce } from "@/hooks/useDebounce";
import { useTheme } from "@/hooks/useTheme";
import {
  builders,
  projects,
  flares,
  conversations,
  hackathons,
  type Builder,
  type Project,
  type Flare,
  type Conversation,
  type Hackathon,
} from "@/mocks/seed";
import { repositories, type RepositoryItem } from "@/mocks/repositories";
import { cn } from "@/lib/utils";
import { TypoCaption } from "@/components/shared/Typography";

const RECENT_SEARCHES_KEY = "devlink-recent-searches";
const MAX_RECENT_SEARCHES = 5;

type SearchCategory =
  "developers" | "projects" | "posts" | "messages" | "hackathons" | "repositories" | "commands";

export interface SearchResultItem {
  id: string;
  category: SearchCategory;
  title: string;
  subtitle: string;
  url: string;
  icon: React.ReactNode;
  badge?: string;
}

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSearchModal({ isOpen, onClose }: GlobalSearchModalProps) {
  const [query, setQuery] = useState("");
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<SearchCategory | "all">("all");
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsContainerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { toggleTheme } = useTheme();

  const debouncedQuery = useDebounce(query, 250);

  const commands = useMemo<SearchResultItem[]>(
    () => [
      {
        id: "cmd-dashboard",
        category: "commands",
        title: "Go to Dashboard",
        subtitle: "Jump to your home dashboard feed",
        url: "/dashboard",
        icon: <LayoutDashboard size={16} className="text-primary" />,
        badge: "Navigation",
      },
      {
        id: "cmd-projects",
        category: "commands",
        title: "Go to Projects",
        subtitle: "Browse and discover active projects",
        url: "/projects",
        icon: <FolderGit2 size={16} className="text-emerald-500" />,
        badge: "Navigation",
      },
      {
        id: "cmd-builders",
        category: "commands",
        title: "Go to Builders",
        subtitle: "Find other developers and collaborators",
        url: "/builders",
        icon: <Users size={16} className="text-blue-500" />,
        badge: "Navigation",
      },
      {
        id: "cmd-flares",
        category: "commands",
        title: "Go to Flares",
        subtitle: "View the community feed and updates",
        url: "/flares",
        icon: <Rss size={16} className="text-amber-500" />,
        badge: "Navigation",
      },
      {
        id: "cmd-hackathons",
        category: "commands",
        title: "Go to Hackathons",
        subtitle: "Join hackathons and team listings",
        url: "/hackathons",
        icon: <Trophy size={16} className="text-yellow-500" />,
        badge: "Navigation",
      },
      {
        id: "cmd-theme",
        category: "commands",
        title: "Toggle Theme",
        subtitle: "Switch between Light and Dark mode",
        url: "action:toggle-theme",
        icon: <Sparkles size={16} className="text-rose-500" />,
        badge: "Action",
      },
    ],
    [],
  );

  // Load recent searches on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
      if (stored) {
        setRecentSearches(JSON.parse(stored));
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Save recent search
  const saveRecentSearch = useCallback((searchTerm: string) => {
    const trimmed = searchTerm.trim();
    if (!trimmed) return;
    setRecentSearches((prev) => {
      const filtered = prev.filter((item) => item.toLowerCase() !== trimmed.toLowerCase());
      const updated = [trimmed, ...filtered].slice(0, MAX_RECENT_SEARCHES);
      try {
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
      } catch {
        // Ignore storage errors
      }
      return updated;
    });
  }, []);

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([]);
    try {
      localStorage.removeItem(RECENT_SEARCHES_KEY);
    } catch {
      // Ignore storage errors
    }
  }, []);

  const removeRecentSearch = useCallback((term: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches((prev) => {
      const updated = prev.filter((item) => item !== term);
      try {
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
      } catch {
        // Ignore storage errors
      }
      return updated;
    });
  }, []);

  // Filter search results across all categories
  const searchResults = useMemo<SearchResultItem[]>(() => {
    const q = debouncedQuery.trim().toLowerCase();
    if (!q) return commands;

    const results: SearchResultItem[] = [];

    // 0. Commands
    commands.forEach((c) => {
      if (c.title.toLowerCase().includes(q) || c.subtitle.toLowerCase().includes(q)) {
        results.push(c);
      }
    });

    // 1. Developers
    builders.forEach((b: Builder) => {
      const matchName = b.name.toLowerCase().includes(q);
      const matchHandle = b.handle.toLowerCase().includes(q);
      const matchSkill = b.skills.some((s) => s.toLowerCase().includes(q));
      const matchRole = b.role.toLowerCase().includes(q);

      if (matchName || matchHandle || matchSkill || matchRole) {
        results.push({
          id: `dev-${b.id}`,
          category: "developers",
          title: b.name,
          subtitle: `@${b.handle} • ${b.role} • ${b.skills.slice(0, 3).join(", ")}`,
          url: `/builders/${b.id}`,
          icon: <Users size={16} className="text-blue-500" />,
          badge: b.role,
        });
      }
    });

    // 2. Projects
    projects.forEach((p: Project) => {
      const matchName = p.name.toLowerCase().includes(q);
      const matchDesc = p.description.toLowerCase().includes(q);
      const matchStack = p.stack.some((s) => s.toLowerCase().includes(q));

      if (matchName || matchDesc || matchStack) {
        results.push({
          id: `proj-${p.id}`,
          category: "projects",
          title: p.name,
          subtitle: `${p.description} • ${p.stack.slice(0, 3).join(", ")}`,
          url: `/projects/${p.id}`,
          icon: <FolderGit2 size={16} className="text-emerald-500" />,
          badge: p.status,
        });
      }
    });

    // 3. Posts
    flares.forEach((f: Flare) => {
      const matchContent = f.content.toLowerCase().includes(q);
      const matchAuthor = f.author.name.toLowerCase().includes(q);
      const matchTag = f.tags.some((t) => t.toLowerCase().includes(q));

      if (matchContent || matchAuthor || matchTag) {
        results.push({
          id: `post-${f.id}`,
          category: "posts",
          title: `Post by ${f.author.name}`,
          subtitle: f.content,
          url: "/flares",
          icon: <Rss size={16} className="text-amber-500" />,
          badge: `#${f.tags[0] || "post"}`,
        });
      }
    });

    // 4. Messages
    conversations.forEach((c: Conversation) => {
      const matchWith = c.with.name.toLowerCase().includes(q);
      const matchPreview = c.preview.toLowerCase().includes(q);

      if (matchWith || matchPreview) {
        results.push({
          id: `msg-${c.id}`,
          category: "messages",
          title: `Message with ${c.with.name}`,
          subtitle: c.preview,
          url: `/messages/${c.id}`,
          icon: <MessageSquare size={16} className="text-purple-500" />,
          badge: c.unread ? `${c.unread} unread` : "Chat",
        });
      }
    });

    // 5. Hackathons
    hackathons.forEach((h: Hackathon) => {
      const matchName = h.name.toLowerCase().includes(q);
      const matchTheme = h.theme.toLowerCase().includes(q);
      const matchDesc = h.description.toLowerCase().includes(q);

      if (matchName || matchTheme || matchDesc) {
        results.push({
          id: `hack-${h.id}`,
          category: "hackathons",
          title: h.name,
          subtitle: `${h.theme} • Prize: ${h.prize} • ${h.description}`,
          url: `/hackathons/${h.id}`,
          icon: <Trophy size={16} className="text-yellow-500" />,
          badge: h.status.replace("_", " "),
        });
      }
    });

    // 6. Repositories
    repositories.forEach((r: RepositoryItem) => {
      const matchName = r.name.toLowerCase().includes(q);
      const matchDesc = r.description.toLowerCase().includes(q);
      const matchLang = r.language.toLowerCase().includes(q);

      if (matchName || matchDesc || matchLang) {
        results.push({
          id: `repo-${r.id}`,
          category: "repositories",
          title: r.name,
          subtitle: `${r.description} • ⭐ ${r.stars}`,
          url: `/projects/${r.projectId}`,
          icon: <GitBranch size={16} className="text-rose-500" />,
          badge: r.language,
        });
      }
    });

    return results;
  }, [debouncedQuery, commands]);

  // Filtered results based on category filter tab
  const filteredResults = useMemo(() => {
    if (activeCategoryFilter === "all") return searchResults;
    return searchResults.filter((item) => item.category === activeCategoryFilter);
  }, [searchResults, activeCategoryFilter]);

  // Handle focus when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    } else {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const handleNavigate = useCallback(
    (targetUrl: string) => {
      onClose();
      if (targetUrl === "action:toggle-theme") {
        toggleTheme();
      } else {
        navigate({ to: targetUrl as unknown as "/flares" });
      }
    },
    [onClose, navigate, toggleTheme],
  );

  // Handle keyboard shortcuts (ArrowUp, ArrowDown, Enter, Escape)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }

      if (filteredResults.length === 0) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev < filteredResults.length - 1 ? prev + 1 : 0));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filteredResults.length - 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        const selected = filteredResults[selectedIndex];
        if (selected) {
          saveRecentSearch(query || selected.title);
          handleNavigate(selected.url);
        }
      }
    },
    [filteredResults, selectedIndex, query, onClose, saveRecentSearch, handleNavigate],
  );

  // Auto-scroll selected item into view
  useEffect(() => {
    if (resultsContainerRef.current) {
      const activeEl = resultsContainerRef.current.querySelector('[data-selected="true"]');
      if (activeEl) {
        activeEl.scrollIntoView({ block: "nearest" });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  const categories: { id: SearchCategory | "all"; label: string }[] = [
    { id: "all", label: "All" },
    { id: "developers", label: "Developers" },
    { id: "projects", label: "Projects" },
    { id: "posts", label: "Posts" },
    { id: "messages", label: "Messages" },
    { id: "hackathons", label: "Hackathons" },
    { id: "repositories", label: "Repositories" },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-16 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-xl border border-border bg-surface shadow-2xl transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header Input */}
        <div className="relative flex items-center border-b border-border px-4 py-3">
          <Search size={18} className="mr-3 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Search Developers, Projects, Posts, Messages, Hackathons, Repositories..."
            className="w-full bg-transparent text-[15px] text-foreground placeholder:text-muted-foreground outline-none"
          />
          {query && (
            <button
              onClick={() => {
                setQuery("");
                inputRef.current?.focus();
              }}
              className="p-1 text-muted-foreground hover:text-foreground"
              aria-label="Clear query"
            >
              <X size={16} />
            </button>
          )}
          <div className="ml-2 hidden items-center gap-1 rounded bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground sm:flex">
            <span>Esc</span>
          </div>
        </div>

        {/* Category Tabs */}
        {query.trim() && (
          <div className="flex items-center gap-1 border-b border-border bg-muted/40 px-3 py-1.5 overflow-x-auto text-[12px]">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => {
                  setActiveCategoryFilter(cat.id);
                  setSelectedIndex(0);
                }}
                className={cn(
                  "rounded-md px-2.5 py-1 font-medium transition-colors whitespace-nowrap",
                  activeCategoryFilter === cat.id
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {cat.label}
              </button>
            ))}
          </div>
        )}

        {/* Search Content Body */}
        <div ref={resultsContainerRef} className="max-h-[380px] overflow-y-auto p-2">
          {/* Empty state: Recent Searches (only if query is empty) */}
          {!query.trim() && recentSearches.length > 0 && (
            <div className="space-y-4 p-2 pb-0">
              <div>
                <div className="flex items-center justify-between px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Clock size={12} /> Recent Searches
                  </span>
                  <button
                    onClick={clearRecentSearches}
                    className="text-muted-foreground hover:text-destructive transition-colors flex items-center gap-1 normal-case cursor-pointer"
                  >
                    <Trash2 size={11} /> Clear
                  </button>
                </div>
                <div className="mt-1 space-y-1">
                  {recentSearches.map((term) => (
                    <div
                      key={term}
                      onClick={() => {
                        setQuery(term);
                        inputRef.current?.focus();
                      }}
                      className="flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-[13px] text-foreground hover:bg-muted/70 transition-colors"
                    >
                      <span className="flex items-center gap-2">
                        <Clock size={14} className="text-muted-foreground" />
                        {term}
                      </span>
                      <button
                        onClick={(e) => removeRecentSearch(term, e)}
                        className="text-muted-foreground hover:text-foreground cursor-pointer"
                        aria-label={`Remove ${term}`}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Results List (both empty query commands & actual search results) */}
          {filteredResults.length > 0 && (
            <div className="space-y-1 p-2">
              {!query.trim() && <TypoCaption as="p">Navigation & Actions</TypoCaption>}
              {filteredResults.map((item, idx) => (
                <div
                  key={item.id}
                  data-selected={idx === selectedIndex}
                  onClick={() => {
                    saveRecentSearch(query || item.title);
                    handleNavigate(item.url);
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={cn(
                    "flex cursor-pointer items-start justify-between rounded-lg p-2.5 transition-colors",
                    idx === selectedIndex
                      ? "bg-primary/10 text-foreground ring-1 ring-primary/30"
                      : "hover:bg-muted/60 text-foreground",
                  )}
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="mt-0.5 rounded-md bg-muted p-1.5 shrink-0">{item.icon}</div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-[13.5px] font-semibold text-foreground">
                          {item.title}
                        </p>
                        {item.badge && <TypoCaption>{item.badge}</TypoCaption>}
                      </div>
                      <TypoCaption as="p">{item.subtitle}</TypoCaption>
                    </div>
                  </div>
                  {idx === selectedIndex && (
                    <CornerDownLeft size={14} className="ml-2 shrink-0 self-center text-primary" />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Popular Suggestions (only if query is empty) */}
          {!query.trim() && (
            <div className="p-2 pt-4">
              <TypoCaption as="p">Popular Suggestions</TypoCaption>
              <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
                {[
                  { label: "React", icon: <Users size={13} /> },
                  { label: "TypeScript", icon: <FolderGit2 size={13} /> },
                  { label: "AI Chatbot", icon: <FolderGit2 size={13} /> },
                  { label: "Hackathons", icon: <Trophy size={13} /> },
                  { label: "FastAPI", icon: <GitBranch size={13} /> },
                  { label: "Next.js", icon: <Users size={13} /> },
                ].map((sug) => (
                  <button
                    key={sug.label}
                    onClick={() => {
                      setQuery(sug.label);
                      inputRef.current?.focus();
                    }}
                    className="flex items-center gap-2 rounded-md border border-border/60 bg-surface px-3 py-2 text-left text-[12px] font-medium text-foreground hover:border-primary/50 hover:bg-primary-soft/30 transition-colors cursor-pointer"
                  >
                    <TypoCaption>{sug.icon}</TypoCaption>
                    {sug.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* No Results Found */}
          {query.trim() && filteredResults.length === 0 && (
            <div className="py-12 text-center text-muted-foreground">
              <Search size={28} className="mx-auto mb-2 opacity-40" />
              <p className="text-[14px] font-medium">No matches found for "{query}"</p>
              <p className="mt-1 text-[12px]">
                Try searching for developers, projects, posts, messages, hackathons, or
                repositories.
              </p>
            </div>
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div className="flex items-center justify-between border-t border-border bg-muted/30 px-4 py-2 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1 font-mono">↑</kbd>
              <kbd className="rounded border border-border bg-surface px-1 font-mono">↓</kbd>{" "}
              navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1 font-mono">↵</kbd> select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="rounded border border-border bg-surface px-1 font-mono">esc</kbd>{" "}
              close
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Command size={12} /> Global Search
          </div>
        </div>
      </div>
    </div>
  );
}
