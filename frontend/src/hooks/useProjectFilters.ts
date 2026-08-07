import { useNavigate, useSearch } from "@tanstack/react-router";
import { projectSearchSchema } from "@/routes/_app.projects";
import { z } from "zod";

export type FilterState = z.infer<typeof projectSearchSchema>;

export function useProjectFilters() {
  const search = useSearch({ strict: false }) as FilterState;
  const navigate = useNavigate();

  const setFilters = (filters: Partial<FilterState>) => {
    navigate({
      to: "/projects",
      search: (prev: Record<string, unknown>) => ({ ...prev, ...filters, page: 1 }),
      replace: true,
    });
  };

  const clearFilters = () => {
    navigate({
      to: "/projects",
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
