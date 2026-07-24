import { MessageSquare, Plus, Search, Sparkles, Menu, Moon, Sun } from "lucide-react";
import {
  Bell,
  MessageSquare,
  Plus,
  Search,
  Sparkles,
  Menu,
  Moon,
  Sun,
  Building2,
  Rss,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { Avatar } from "@/components/shared/primitives";
import { currentUser } from "@/mocks/seed";
import { currentUser, builders, projects, flares } from "@/mocks/seed";
import { useTheme } from "@/hooks/useTheme";
import { NotificationCenter } from "@/components/shared/NotificationCenter";
import { useState } from "react";

const organizations = [
  {
    id: "devlink-org",
    name: "DevLink",
    description: "The developer portfolio & project collaboration network.",
    hiring: true,
    members_count: 12,
    projects_count: 5,
  },
];

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { isDark, toggleTheme } = useTheme();
  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  const normalizedQuery = query.trim().toLowerCase();

  const developerSuggestions = normalizedQuery
    ? builders
        .filter(
          (builder) =>
            builder.name.toLowerCase().includes(normalizedQuery) ||
            builder.skills.some((skill) => skill.toLowerCase().includes(normalizedQuery)),
        )
        .slice(0, 3)
    : [];

  const projectSuggestions = normalizedQuery
    ? projects
        .filter(
          (project) =>
            project.name.toLowerCase().includes(normalizedQuery) ||
            project.stack.some((tech) => tech.toLowerCase().includes(normalizedQuery)),
        )
        .slice(0, 3)
    : [];

  const postSuggestions = normalizedQuery
    ? flares
        .filter(
          (flare) =>
            flare.author.name.toLowerCase().includes(normalizedQuery) ||
            flare.content.toLowerCase().includes(normalizedQuery) ||
            flare.tags.some((tag) => tag.toLowerCase().includes(normalizedQuery)),
        )
        .slice(0, 3)
    : [];

  const organizationSuggestions = normalizedQuery
    ? organizations
        .filter(
          (org) =>
            org.name.toLowerCase().includes(normalizedQuery) ||
            org.description.toLowerCase().includes(normalizedQuery),
        )
        .slice(0, 3)
    : [];

  const hasSuggestions =
    developerSuggestions.length > 0 ||
    projectSuggestions.length > 0 ||
    postSuggestions.length > 0 ||
    organizationSuggestions.length > 0;

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur">
      <button
        onClick={onMenu}
        aria-label="Open menu"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border text-muted-foreground hover:bg-muted lg:hidden"
      >
        <Menu size={16} />
      </button>

      <div className="relative min-w-0 flex-1 max-w-xl">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          type="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => {
            if (query.trim()) setShowSuggestions(true);
          }}
          placeholder="Search developers, projects, posts, organizations…"
          className="w-full rounded-md border border-border bg-surface py-[7px] pl-9 pr-3 text-[13px] text-foreground placeholder:text-muted-foreground outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        {showSuggestions && normalizedQuery && (
          <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-96 overflow-y-auto rounded-md border border-border bg-surface p-2 shadow-lg">
            {hasSuggestions ? (
              <div className="space-y-3">
                {developerSuggestions.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Developers
                    </p>

                    {developerSuggestions.map((builder) => (
                      <Link
                        key={builder.id}
                        to="/builders/$builderId"
                        params={{ builderId: builder.id }}
                        onClick={() => {
                          setQuery("");
                          setShowSuggestions(false);
                        }}
                        className="flex items-center gap-2 rounded-md px-2 py-2 text-[13px] text-foreground hover:bg-muted"
                      >
                        <img src={builder.avatar} alt="" className="h-7 w-7 rounded-full" />
                        <div className="min-w-0">
                          <p className="truncate font-medium">{builder.name}</p>
                          <p className="truncate text-[11px] text-muted-foreground">
                            {builder.role}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}

                {projectSuggestions.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Projects
                    </p>

                    {projectSuggestions.map((project) => (
                      <Link
                        key={project.id}
                        to="/projects/$projectId"
                        params={{ projectId: project.id }}
                        onClick={() => {
                          setQuery("");
                          setShowSuggestions(false);
                        }}
                        className="flex items-center gap-2 rounded-md px-2 py-2 text-[13px] text-foreground hover:bg-muted"
                      >
                        <span className="grid h-7 w-7 place-items-center rounded-md bg-muted">
                          {project.icon}
                        </span>

                        <span className="truncate font-medium">{project.name}</span>
                      </Link>
                    ))}
                  </div>
                )}

                {postSuggestions.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Posts
                    </p>

                    {postSuggestions.map((post) => (
                      <Link
                        key={post.id}
                        to="/flares"
                        onClick={() => {
                          setQuery("");
                          setShowSuggestions(false);
                        }}
                        className="flex items-start gap-2 rounded-md px-2 py-2 text-[13px] text-foreground hover:bg-muted"
                      >
                        <span className="mt-0.5 text-muted-foreground">
                          <Rss size={14} />
                        </span>
                        <div className="min-w-0">
                          <p className="truncate font-medium">{post.author.name}</p>
                          <p className="truncate text-[11px] text-muted-foreground">
                            {post.content}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}

                {organizationSuggestions.length > 0 && (
                  <div>
                    <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      Organizations
                    </p>

                    {organizationSuggestions.map((org) => (
                      <Link
                        key={org.id}
                        to="/organizations/$orgId"
                        params={{ orgId: org.id }}
                        onClick={() => {
                          setQuery("");
                          setShowSuggestions(false);
                        }}
                        className="flex items-center gap-2 rounded-md px-2 py-2 text-[13px] text-foreground hover:bg-muted"
                      >
                        <span className="grid h-7 w-7 place-items-center rounded-md bg-muted text-muted-foreground">
                          <Building2 size={14} />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium">{org.name}</p>
                          <p className="truncate text-[11px] text-muted-foreground">
                            {org.members_count} members · {org.projects_count} projects
                          </p>
                        </div>
                        {org.hiring && (
                          <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">
                            Hiring
                          </span>
                        )}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="px-3 py-4 text-center text-[12px] text-muted-foreground">
                No suggestions found for "{query}"
              </p>
            )}
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
        <NotificationCenter />
        <IconButton to="/messages" count={3}>
          <MessageSquare size={16} />
        </IconButton>
      </div>

      <Link
        to="/profile/$username"
        params={{ username: currentUser.handle }}
        className="ml-1 flex items-center gap-2 rounded-md p-1 hover:bg-muted"
      >
        <Avatar src={currentUser.avatar} alt={currentUser.name} name={currentUser.name} size={32} />
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
