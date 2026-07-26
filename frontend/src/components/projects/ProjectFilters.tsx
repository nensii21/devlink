import { useNavigate, useRouterState } from "@tanstack/react-router";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const LANGUAGES = ["All", "JavaScript", "TypeScript", "Python", "Java", "Go", "Rust"];
const EXPERIENCES = ["Beginner", "Intermediate", "Advanced"];
const REMOTE_OPTIONS = ["All", "Remote", "Hybrid", "Onsite"];
const PAID_OPTIONS = ["All", "Paid", "Unpaid"];
const OPENSOURCE_OPTIONS = ["All", "Yes", "No"];
const TECH_STACKS = [
  "React",
  "Next.js",
  "Node.js",
  "Express",
  "MongoDB",
  "PostgreSQL",
  "Prisma",
  "Docker",
  "AWS",
  "Python",
  "AI/ML",
];

interface FilterSectionProps {
  title: string;
  options: readonly string[];
  value: string;
  onChange: (val: string) => void;
}

function FilterDropdown({ title, options, value, onChange }: FilterSectionProps) {
  return (
    <div className="relative inline-block text-left mr-3 mb-3">
      <div className="flex flex-col">
        <label className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-1">
          {title}
        </label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export function ProjectFilters() {
  const navigate = useNavigate({ from: "/projects" });
  const search = useRouterState({
    select: (state) => state.location.search as Record<string, string>,
  });

  const language = search.language || "All";
  const experience = search.experience || "";
  const remote = search.remote === "true" ? "Remote" : search.remote === "false" ? "Onsite" : "All";
  const paid = search.paid === "true" ? "Paid" : search.paid === "false" ? "Unpaid" : "All";
  const opensource =
    search.opensource === "true" ? "Yes" : search.opensource === "false" ? "No" : "All";
  const tech = search.tech || "";

  const updateSearch = (newParams: Record<string, string | undefined>) => {
    navigate({
      search: (prev: Record<string, unknown>) => {
        const updated: Record<string, unknown> = { ...prev, ...newParams };
        Object.keys(updated).forEach((key) => {
          if (updated[key] === undefined || updated[key] === "" || updated[key] === "All") {
            delete updated[key];
          }
        });
        if (newParams.remote === undefined) delete updated.remote;
        if (newParams.paid === undefined) delete updated.paid;
        if (newParams.opensource === undefined) delete updated.opensource;

        return updated;
      },
      replace: true,
    });
  };

  const clearFilters = () => {
    navigate({
      search: (prev: Record<string, unknown>) => {
        const { language, experience, remote, paid, opensource, tech, ...rest } = prev;
        return rest;
      },
      replace: true,
    });
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 my-4">
      <div className="mb-2">
        <h3 className="text-[14px] font-semibold text-foreground flex items-center gap-2">
          Search Projects
        </h3>
      </div>

      <div className="flex flex-wrap items-end">
        <FilterDropdown
          title="Language"
          options={LANGUAGES}
          value={language}
          onChange={(val) => updateSearch({ language: val === "All" ? undefined : val })}
        />

        <div className="relative inline-block text-left mr-3 mb-3">
          <div className="flex flex-col">
            <label className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-1">
              Experience
            </label>
            <select
              value={experience}
              onChange={(e) => updateSearch({ experience: e.target.value })}
              className="rounded-md border border-border bg-surface px-3 py-1.5 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            >
              <option value="">All</option>
              {EXPERIENCES.map((opt) => (
                <option key={opt} value={opt.toLowerCase()}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        </div>

        <FilterDropdown
          title="Remote"
          options={REMOTE_OPTIONS}
          value={remote}
          onChange={(val) => {
            const mapped = val === "Remote" ? "true" : val === "Onsite" ? "false" : undefined;
            updateSearch({ remote: mapped });
          }}
        />

        <FilterDropdown
          title="Paid"
          options={PAID_OPTIONS}
          value={paid}
          onChange={(val) => {
            const mapped = val === "Paid" ? "true" : val === "Unpaid" ? "false" : undefined;
            updateSearch({ paid: mapped });
          }}
        />

        <FilterDropdown
          title="Open Source"
          options={OPENSOURCE_OPTIONS}
          value={opensource}
          onChange={(val) => {
            const mapped = val === "Yes" ? "true" : val === "No" ? "false" : undefined;
            updateSearch({ opensource: mapped });
          }}
        />

        <div className="relative inline-block text-left mr-3 mb-3">
          <div className="flex flex-col">
            <label className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-1">
              Tech Stack
            </label>
            <select
              value={tech}
              onChange={(e) => updateSearch({ tech: e.target.value })}
              className="rounded-md border border-border bg-surface px-3 py-1.5 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            >
              <option value="">All</option>
              {TECH_STACKS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-3 flex items-center h-full">
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:border-destructive/50 hover:text-destructive focus:outline-none focus:ring-2 focus:ring-destructive/20"
          >
            <X size={13} /> Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
}
