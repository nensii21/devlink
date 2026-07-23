import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, TagChip, Avatar } from "@/components/shared/primitives";
import { builders, projects, flares } from "@/mocks/seed";
import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { Search, X } from "lucide-react";

const tabs = ["Developers", "Projects", "Skills", "Flares"] as const;
type Tab = (typeof tabs)[number];

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

type SearchParams = {
  q?: string;
};

export const Route = createFileRoute("/_app/search")({
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return {
      q: (search.q as string) || "",
    };
  },
  head: () => ({
    meta: [
      { title: "Search — DevLink" },
      {
        name: "description",
        content: "Global search across developers, projects, skills and flares.",
      },
    ],
  }),
  component: SearchPage,
});

function SearchPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const q = search.q || "";

  const [inputValue, setInputValue] = useState(q);
  const [isFocused, setIsFocused] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<Tab>("Developers");

  useEffect(() => {
    setInputValue(q);
  }, [q]);

  const selectSkill = (skill: string) => {
    setInputValue(skill);
    setIsFocused(false);
    navigate({
      search: (prev) => ({ ...prev, q: skill }),
      replace: true,
    });
  };

  const clearSearch = () => {
    setInputValue("");
    navigate({
      search: (prev) => ({ ...prev, q: "" }),
      replace: true,
    });
  };

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
    ? ALL_SKILLS.filter(
        (skill) =>
          skill.toLowerCase().includes(inputValue.toLowerCase()) &&
          skill.toLowerCase() !== q.toLowerCase(),
      ).slice(0, 8)
    : [];

  useEffect(() => {
    setHighlightedIndex(-1);
  }, [inputValue]);

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

  const devs = builders.filter((b) => {
    if (!q) return true;
    return b.skills.some((s) => s.toLowerCase().includes(q.toLowerCase()));
  });

  const projs = projects.filter((p) => {
    if (!q) return true;
    return p.stack.some((s) => s.toLowerCase().includes(q.toLowerCase()));
  });

  const skillSet = ALL_SKILLS.filter((s) => {
    if (!q) return true;
    return s.toLowerCase().includes(q.toLowerCase());
  });

  const fls = flares.filter((f) => {
    if (!q) return true;
    return (
      f.tags.some((t) => t.toLowerCase().includes(q.toLowerCase())) ||
      f.author.skills.some((s) => s.toLowerCase().includes(q.toLowerCase()))
    );
  });

  return (
    <div className="space-y-4">
      <div ref={containerRef} className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />

        <input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search DevLink…"
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-10 text-[14px] outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          autoFocus
        />

        {inputValue && (
          <button
            type="button"
            onClick={clearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X size={16} />
          </button>
        )}

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
      <div className="flex items-center gap-1 rounded-md border border-border bg-surface p-0.5">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded px-3 py-1.5 text-[12px] font-medium transition-colors",
              tab === t
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Developers" && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {devs.length === 0 ? (
            <p className="col-span-full py-8 text-center text-[13px] text-muted-foreground">
              No developers match your skill search.
            </p>
          ) : (
            devs.map((b) => (
              <Link key={b.id} to="/builders/$builderId" params={{ builderId: b.id }}>
                <Card interactive className="flex items-center gap-3 p-3">
                  <Avatar src={b.avatar} alt={b.name} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-semibold text-foreground">{b.name}</p>
                    <p className="truncate text-[12px] text-muted-foreground">{b.role}</p>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}
      {tab === "Projects" && (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {projs.length === 0 ? (
            <p className="col-span-full py-8 text-center text-[13px] text-muted-foreground">
              No projects match your skill search.
            </p>
          ) : (
            projs.map((p) => (
              <Link key={p.id} to="/projects/$projectId" params={{ projectId: p.id }}>
                <Card interactive className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-10 w-10 place-items-center rounded-md bg-muted text-xl">
                      {p.icon}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold text-foreground">{p.name}</p>
                      <p className="truncate text-[12px] text-muted-foreground">
                        {p.stack.join(" · ")}
                      </p>
                    </div>
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      )}
      {tab === "Skills" && (
        <Card className="p-4">
          {skillSet.length === 0 ? (
            <p className="py-4 text-center text-[13px] text-muted-foreground">
              No matching skills found.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {skillSet.map((s) => (
                <button key={s} onClick={() => selectSkill(s)}>
                  <TagChip className="text-[12px] cursor-pointer hover:bg-primary/10 hover:text-primary transition-colors">
                    {s}
                  </TagChip>
                </button>
              ))}
            </div>
          )}
        </Card>
      )}
      {tab === "Flares" && (
        <div className="space-y-3">
          {fls.length === 0 ? (
            <p className="py-8 text-center text-[13px] text-muted-foreground">
              No flares match your skill search.
            </p>
          ) : (
            fls.map((f) => (
              <Card key={f.id} className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-semibold text-foreground">{f.author.name}</p>
                  <div className="flex gap-1">
                    {f.tags.map((t) => (
                      <span
                        key={t}
                        className="text-[10px] text-primary bg-primary/5 px-1.5 py-0.5 rounded"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="mt-1.5 text-[13px] text-foreground">{f.content}</p>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
