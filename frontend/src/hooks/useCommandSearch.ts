"use client";

import * as React from "react";

import { searchProjects, searchUsers, type ProjectSearchResult, type DeveloperSearchResult } from "@/lib/api";

import { includesCaseInsensitive } from "@/lib/commandSearchUtils";



export type CommandPalettePageId =
  | "dashboard"
  | "projects"
  | "builders"
  | "messages"
  | "notifications"
  | "settings";

export type CommandPaletteRouteResult = {
  id: string;
  title: string;
  description?: string;
  group: "pages" | "projects" | "developers";
};

const STATIC_PAGES: Array<{ id: CommandPalettePageId; title: string; matchTokens: string[] }> = [
  { id: "dashboard", title: "Dashboard", matchTokens: ["dashboard", "home"] },
  { id: "projects", title: "Projects", matchTokens: ["projects", "project"] },
  { id: "builders", title: "Builder's Flare", matchTokens: ["flare", "builder's flare", "builders"] },
  { id: "messages", title: "Messages", matchTokens: ["messages", "inbox", "chat"] },
  {
    id: "notifications",
    title: "Notifications",
    matchTokens: ["notifications", "alerts", "updates"],
  },
  { id: "settings", title: "Settings", matchTokens: ["settings", "preferences", "profile"] },
];

function normalizeQuery(query: string): string {
  return query.trim();
}

function toDeveloperResult(user: DeveloperSearchResult): CommandPaletteRouteResult {

  return {
    id: user.id,
    title: user.username,
    description: user.headline,
    group: "developers",
  };
}

function toProjectResult(project: ProjectSearchResult): CommandPaletteRouteResult {

  return {
    id: project.id,
    title: project.title,
    description: project.slug,
    group: "projects",
  };
}

export type UseCommandSearchResult = {
  pages: CommandPaletteRouteResult[];
  projects: CommandPaletteRouteResult[];
  developers: CommandPaletteRouteResult[];
  isLoading: boolean;
  error: Error | null;
};

export function useCommandSearch(query: string): UseCommandSearchResult {
  const [debouncedQuery, setDebouncedQuery] = React.useState<string>(() => normalizeQuery(query));
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<Error | null>(null);

  const [projectsResults, setProjectsResults] = React.useState<CommandPaletteRouteResult[]>([]);
  const [developersResults, setDevelopersResults] = React.useState<CommandPaletteRouteResult[]>([]);

  React.useEffect(() => {
    const next = normalizeQuery(query);
    const handle = window.setTimeout(() => setDebouncedQuery(next), 250);
    return () => window.clearTimeout(handle);
  }, [query]);



  const pages = React.useMemo<CommandPaletteRouteResult[]>(() => {
    const q = debouncedQuery;
    if (!q) {
      return STATIC_PAGES.map((p) => ({ id: p.id, title: p.title, group: "pages" }));
    }

    return STATIC_PAGES.filter((p) =>
      p.matchTokens.some((t) => includesCaseInsensitive(t, q)),
    ).map((p) => ({
      id: p.id,
      title: p.title,
      group: "pages",
    }));
  }, [debouncedQuery]);

  React.useEffect(() => {
    const q = debouncedQuery;

    // Keep these values deterministic for short queries.
    if (q.length < 2) {
      setProjectsResults([]);
      setDevelopersResults([]);
      setIsLoading(false);
      setError(null);
      return;
    }


    const controller = new AbortController();

    setIsLoading(true);
    setError(null);

    Promise.all([
      searchProjects(q, controller.signal),
      searchUsers(q, controller.signal),
    ])
      .then(([projects, users]) => {
        if (controller.signal.aborted) return;

        setProjectsResults(projects.map(toProjectResult));
        setDevelopersResults(users.map(toDeveloperResult));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;

        const nextErr =
          err instanceof Error ? err : new Error("Unknown error while searching command palette.");
        setError(nextErr);
        setProjectsResults([]);
        setDevelopersResults([]);
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setIsLoading(false);
      });

    return () => controller.abort();
  }, [debouncedQuery]);

  return {
    pages,
    projects: projectsResults,
    developers: developersResults,
    isLoading,
    error,
  };
}
