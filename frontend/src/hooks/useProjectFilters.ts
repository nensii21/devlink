import { useNavigate, useSearch } from "@tanstack/react-router";
import { projectSearchSchema } from "@/routes-hold/_app.projects";
import { z } from "zod";

export type FilterState = z.infer<typeof projectSearchSchema>;

/**
 * The router hands the search updater whatever is currently in the URL, which
 * is wider than `FilterState` — other routes contribute their own keys, and a
 * hand-edited URL can contain anything. We only ever read our own keys off it
 * and pass the rest through untouched, so an index signature describes it more
 * honestly than `any` did.
 */
type SearchRecord = Record<string, unknown>;

export function useProjectFilters() {
  const search = useSearch({ strict: false }) as FilterState;
  const navigate = useNavigate();

  const setFilters = (filters: Partial<FilterState>) => {
    navigate({
      to: "/projects",
      search: (prev: SearchRecord) => ({ ...prev, ...filters, page: 1 }),
      search: (prev: Record<string, unknown>) => ({ ...prev, ...filters, page: 1 }),
      replace: true,
    });
  };

  const clearFilters = () => {
    navigate({
      to: "/projects",
      search: (prev: SearchRecord) => {
        // Drop every filter key, keep anything else the URL was carrying, and
        // send the user back to the first page of unfiltered results.
        const {
          language: _language,
          experience: _experience,
          tech: _tech,
          remote: _remote,
          paid: _paid,
          opensource: _opensource,
          ...rest
        } = prev;
      search: (prev: Record<string, unknown>) => {
        const { language, experience, tech, remote, paid, opensource, ...rest } = prev;
        return { ...rest, page: 1 };
      },
      replace: true,
    });
  };

  const hasActiveFilters =
    (search.language && search.language.length > 0) ||
    (search.experience && search.experience.length > 0) ||
    (search.tech && search.tech.length > 0) ||
    search.remote !== undefined ||
    search.paid !== undefined ||
    search.opensource !== undefined;

  const chipFilterCount = [
    ...(search.language || []),
    ...(search.experience || []),
    ...(search.tech || []),
    ...(search.remote !== undefined ? ["remote"] : []),
    ...(search.paid !== undefined ? ["paid"] : []),
    ...(search.opensource !== undefined ? ["opensource"] : []),
  ].length;

  return {
    filters: search,
    setFilters,
    clearFilters,
    hasActiveFilters,
    chipFilterCount,
  };
}
