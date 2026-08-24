import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { z } from "zod";
import { projectsService } from "@/services";
import { Card, TagChip, AnimatedCard, EmptyState } from "@/components/shared/primitives";
import { ProjectOverviewCard } from "@/components/projects/ProjectOverviewCard";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";
import {
  Search,
  Star,
  Eye,
  TrendingUp,
  Sparkles,
  Activity,
  Clock,
  ChevronLeft,
  ChevronRight,
  X,
  Compass,
  Laptop,
  Moon,
  Sun,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { APP_LOGO } from "@/lib/logo";
import { useTheme } from "@/hooks/useTheme";

export const showcaseSearchSchema = z.object({
  page: z.number().catch(1).optional(),
  q: z.string().optional(),
  language: z.string().optional(),
  difficulty: z.string().optional(),
  tab: z.enum(["all", "featured", "trending", "recent", "active"]).catch("all").optional(),
});

export const Route = createFileRoute("/showcase")({
  head: () => ({
    meta: [
      { title: "Project Showcase — DevLink" },
      { name: "description", content: "Explore featured, trending, recently launched, and most active projects on DevLink." },
      { property: "og:title", content: "Project Showcase — DevLink" },
      { property: "og:description", content: "Discover featured, trending, and active projects built by DevLink builders." },
    ],
  }),
  validateSearch: showcaseSearchSchema,
  component: ProjectShowcasePage,
});

function ProjectShowcasePage() {
  const { isDark, toggleTheme } = useTheme();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  const page = search.page || 1;
  const q = search.q || "";
  const language = search.language || "";
  const difficulty = search.difficulty || "";
  const activeTab = search.tab || "all";

  const ITEMS_PER_PAGE = 6;

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsService.list(),
  });

  // Extract unique languages and difficulties for filter options
  const languageOptions = useMemo(() => {
    const langs = new Set<string>();
    projects.forEach((p) => {
      if (p.language) langs.add(p.language);
    });
    return Array.from(langs);
  }, [projects]);

  // Derived Project Categories / Tabs
  const filteredAndSortedProjects = useMemo(() => {
    let result = [...projects];

    // Filter by Tab
    if (activeTab === "featured") {
      result = result.filter((p) => (p.stars || 0) >= 15);
    } else if (activeTab === "trending") {
      result = result.sort((a, b) => (b.views || 0) - (a.views || 0));
    } else if (activeTab === "recent") {
      result = result.filter((p) => p.status === "completed" || (p.progress || 0) >= 70);
    } else if (activeTab === "active") {
      result = result.filter((p) => (p.members || 0) >= 4);
    }

    // Filter by Search Query
    if (q) {
      const query = q.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.description.toLowerCase().includes(query) ||
          p.stack?.some((t) => t.toLowerCase().includes(query)),
      );
    }

    // Filter by Language
    if (language) {
      result = result.filter((p) => p.language === language);
    }

    // Filter by Difficulty
    if (difficulty) {
      result = result.filter((p) => p.difficulty === difficulty);
    }

    return result;
  }, [projects, activeTab, q, language, difficulty]);

  // Pagination calculations
  const totalPages = Math.ceil(filteredAndSortedProjects.length / ITEMS_PER_PAGE);
  const paginatedProjects = useMemo(() => {
    const startIndex = (page - 1) * ITEMS_PER_PAGE;
    return filteredAndSortedProjects.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredAndSortedProjects, page]);

  // Update query state safely
  const updateSearch = (updates: Partial<z.infer<typeof showcaseSearchSchema>>) => {
    navigate({
      search: (prev) => ({
        ...prev,
        ...updates,
        // Reset to page 1 on filter/tab changes
        page: updates.page !== undefined ? updates.page : 1,
      }),
      replace: true,
    });
  };

  const handleClearFilters = () => {
    navigate({
      search: () => ({
        page: 1,
        q: undefined,
        language: undefined,
        difficulty: undefined,
        tab: "all",
      }),
      replace: true,
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Public Header */}
      <header className="sticky top-0 z-20 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <img src={APP_LOGO} alt="" className="h-9 w-9 rounded-md" />
            <span className="text-[20px] font-bold tracking-tight text-foreground">DevLink</span>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              to="/showcase"
              className="text-[13px] font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              Showcase
            </Link>
            <Link
              to="/builders"
              className="text-[13px] font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Builders
            </Link>
            <button
              type="button"
              onClick={toggleTheme}
              className="grid h-9 w-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link
              to="/auth"
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-[12px] font-semibold text-primary-foreground transition-all duration-200 hover:opacity-90 cursor-pointer"
            >
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 sm:px-6 py-8 space-y-8">
        {/* Hero Section */}
        <section className="text-center py-6 md:py-10 space-y-4 rounded-3xl bg-radial-gradient relative overflow-hidden border border-border/40">
          <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none" />
          <div className="relative z-10 space-y-3">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
              <Compass size={14} className="animate-spin-slow" /> Project Hub
            </div>
            <TypoHeading as="h1" className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight">
              Project Showcase
            </TypoHeading>
            <TypoCaption as="p" className="text-sm sm:text-base max-w-xl mx-auto text-muted-foreground">
              Discover, explore, and collaborate on trending applications built by developers across the world.
            </TypoCaption>
          </div>
        </section>

        {/* Stats Grid at a glance */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4 flex items-center gap-3 bg-surface/50 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="text-xl font-bold">{projects.filter(p => (p.stars || 0) >= 15).length}</div>
              <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Featured</div>
            </div>
          </Card>
          <Card className="p-4 flex items-center gap-3 bg-surface/50 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-500">
              <TrendingUp size={20} />
            </div>
            <div>
              <div className="text-xl font-bold">{projects.length}</div>
              <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Total projects</div>
            </div>
          </Card>
          <Card className="p-4 flex items-center gap-3 bg-surface/50 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500">
              <Clock size={20} />
            </div>
            <div>
              <div className="text-xl font-bold">{projects.filter(p => p.status === "completed" || (p.progress || 0) >= 70).length}</div>
              <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Recently Launched</div>
            </div>
          </Card>
          <Card className="p-4 flex items-center gap-3 bg-surface/50 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-500">
              <Activity size={20} />
            </div>
            <div>
              <div className="text-xl font-bold">{projects.filter(p => (p.members || 0) >= 4).length}</div>
              <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Active Teams</div>
            </div>
          </Card>
        </section>

        {/* Search, Filter & Tabs Section */}
        <section className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Filter Tabs */}
            <div className="flex flex-wrap gap-1 p-1 bg-muted rounded-xl w-fit">
              <button
                type="button"
                onClick={() => updateSearch({ tab: "all" })}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                  activeTab === "all" ? "bg-surface shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                All Projects
              </button>
              <button
                type="button"
                onClick={() => updateSearch({ tab: "featured" })}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1 ${
                  activeTab === "featured" ? "bg-surface shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles size={12} className="text-amber-500 fill-amber-500/20" /> Featured
              </button>
              <button
                type="button"
                onClick={() => updateSearch({ tab: "trending" })}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1 ${
                  activeTab === "trending" ? "bg-surface shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <TrendingUp size={12} className="text-primary" /> Trending
              </button>
              <button
                type="button"
                onClick={() => updateSearch({ tab: "recent" })}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1 ${
                  activeTab === "recent" ? "bg-surface shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Clock size={12} className="text-emerald-500" /> Recently Launched
              </button>
              <button
                type="button"
                onClick={() => updateSearch({ tab: "active" })}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1 ${
                  activeTab === "active" ? "bg-surface shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Activity size={12} className="text-rose-500" /> Most Active
              </button>
            </div>

            {/* Reset Filters Option */}
            {(q || language || difficulty || activeTab !== "all") && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="text-xs font-semibold text-primary hover:text-primary/80 flex items-center gap-1 transition-colors ml-auto md:ml-0"
              >
                <X size={12} /> Clear all filters
              </button>
            )}
          </div>

          {/* Filters Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-surface/50 border border-border/50 p-4 rounded-2xl">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search projects or stack..."
                value={q}
                onChange={(e) => updateSearch({ q: e.target.value || undefined })}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-border/80 bg-background text-[13px] placeholder:text-muted-foreground focus:outline-none focus:border-primary/80 focus:ring-1 focus:ring-primary/80 transition-all"
              />
            </div>

            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => updateSearch({ language: e.target.value || undefined })}
              className="px-3 py-2 rounded-xl border border-border/80 bg-background text-[13px] focus:outline-none focus:border-primary/80 transition-all"
            >
              <option value="">All Languages</option>
              {languageOptions.map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>

            {/* Difficulty Selector */}
            <select
              value={difficulty}
              onChange={(e) => updateSearch({ difficulty: e.target.value || undefined })}
              className="px-3 py-2 rounded-xl border border-border/80 bg-background text-[13px] focus:outline-none focus:border-primary/80 transition-all"
            >
              <option value="">All Difficulties</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>
        </section>

        {/* Project Showcase Grid */}
        <section className="relative min-h-[300px]">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="p-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-muted rounded-xl animate-pulse" />
                    <div className="space-y-2 flex-1">
                      <div className="h-4 w-1/2 bg-muted rounded animate-pulse" />
                      <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
                    </div>
                  </div>
                  <div className="h-16 bg-muted rounded-xl animate-pulse" />
                  <div className="flex justify-between items-center">
                    <div className="h-4 w-1/4 bg-muted rounded animate-pulse" />
                    <div className="h-4 w-1/4 bg-muted rounded animate-pulse" />
                  </div>
                </Card>
              ))}
            </div>
          ) : paginatedProjects.length === 0 ? (
            <EmptyState
              illustration="no-results"
              title="No projects match your criteria"
              desc="Try adjusting your query, filters, or selected tab to find projects."
              action={
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90"
                >
                  Reset Showcase Filters
                </button>
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <AnimatePresence mode="popLayout">
                {paginatedProjects.map((project, index) => (
                  <AnimatedCard key={project.id} index={index} interactive className="h-full">
                    <ProjectOverviewCard project={project} />
                  </AnimatedCard>
                ))}
              </AnimatePresence>
            </div>
          )}
        </section>

        {/* Pagination Section */}
        {totalPages > 1 && (
          <section className="flex items-center justify-center gap-2 pt-6">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => updateSearch({ page: page - 1 })}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground transition-all hover:bg-muted hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Previous page"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-xs font-semibold text-muted-foreground px-3">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => updateSearch({ page: page + 1 })}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-muted-foreground transition-all hover:bg-muted hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Next page"
            >
              <ChevronRight size={16} />
            </button>
          </section>
        )}
      </main>

      {/* Public Footer */}
      <footer className="border-t border-border/60 bg-surface/30 py-8 mt-12 text-center text-xs text-muted-foreground">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p>© {new Date().getFullYear()} DevLink. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
