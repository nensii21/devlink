import { useState, useEffect, useRef, useMemo } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface SkillItem {
  name: string;
  category: "Frontend" | "Backend" | "AI / ML" | "Mobile" | "DevOps" | "Database" | "Web3";
  buildersCount: number;
  projectsCount: number;
  trending?: boolean;
}

const POPULAR_SKILLS: SkillItem[] = [
  { name: "React", category: "Frontend", buildersCount: 42, projectsCount: 28, trending: true },
  {
    name: "TypeScript",
    category: "Frontend",
    buildersCount: 38,
    projectsCount: 24,
    trending: true,
  },
  { name: "Next.js", category: "Frontend", buildersCount: 35, projectsCount: 22, trending: true },
  { name: "Python", category: "Backend", buildersCount: 30, projectsCount: 19, trending: true },
  { name: "Node.js", category: "Backend", buildersCount: 29, projectsCount: 20 },
  { name: "PyTorch", category: "AI / ML", buildersCount: 18, projectsCount: 12, trending: true },
  {
    name: "OpenAI / LLMs",
    category: "AI / ML",
    buildersCount: 25,
    projectsCount: 16,
    trending: true,
  },
  { name: "PostgreSQL", category: "Database", buildersCount: 22, projectsCount: 15 },
  { name: "MongoDB", category: "Database", buildersCount: 20, projectsCount: 14 },
  { name: "Docker", category: "DevOps", buildersCount: 19, projectsCount: 13 },
  { name: "Kubernetes", category: "DevOps", buildersCount: 14, projectsCount: 9 },
  { name: "AWS", category: "DevOps", buildersCount: 24, projectsCount: 17 },
  { name: "Flutter", category: "Mobile", buildersCount: 16, projectsCount: 10 },
  { name: "React Native", category: "Mobile", buildersCount: 15, projectsCount: 9 },
  { name: "Tailwind CSS", category: "Frontend", buildersCount: 33, projectsCount: 25 },
  { name: "Solidity", category: "Web3", buildersCount: 11, projectsCount: 7 },
  { name: "Go", category: "Backend", buildersCount: 17, projectsCount: 11 },
  { name: "FastAPI", category: "Backend", buildersCount: 19, projectsCount: 12 },
];

const CATEGORY_COLORS: Record<string, string> = {
  Frontend: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  Backend: "bg-green-500/10 text-green-500 border-green-500/20",
  "AI / ML": "bg-purple-500/10 text-purple-500 border-purple-500/20",
  Mobile: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  DevOps: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  Database: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  Web3: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
};

interface SkillSuggestionDropdownProps {
  query: string;
  isOpen: boolean;
  onSelectSkill: (skillName: string) => void;
  onClose: () => void;
  className?: string;
}

export function SkillSuggestionDropdown({
  query,
  isOpen,
  onSelectSkill,
  onClose,
  className,
}: SkillSuggestionDropdownProps) {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredSkills = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      return [];
    }
    return POPULAR_SKILLS.filter(
      (skill) => skill.name.toLowerCase().includes(q) || skill.category.toLowerCase().includes(q),
    ).slice(0, 8);
  }, [query]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [filteredSkills]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredSkills.length));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(
          (prev) => (prev - 1 + filteredSkills.length) % Math.max(1, filteredSkills.length),
        );
      } else if (e.key === "Enter" && filteredSkills[selectedIndex]) {
        e.preventDefault();
        onSelectSkill(filteredSkills[selectedIndex].name);
      } else if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredSkills, selectedIndex, onSelectSkill, onClose]);

  if (!isOpen || !query.trim() || filteredSkills.length === 0) return null;

  return (
    <div
      ref={dropdownRef}
      className={cn(
        "absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-xl border border-border bg-surface/95 p-2 shadow-2xl backdrop-blur-md transition-all animate-in fade-in-50 zoom-in-95",
        className,
      )}
    >
      <div className="flex items-center justify-between px-2.5 py-1.5 border-b border-border/50 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
        <div className="flex items-center gap-1.5">
          <Sparkles size={13} className="text-primary" />
          <span>{query.trim() ? "Skill Suggestions" : "suggested skills"}</span>
        </div>
        <span className="text-[10px] lowercase font-normal opacity-75">
          {filteredSkills.length} matches
        </span>
      </div>

      {filteredSkills.length === 0 ? (
        <div className="py-6 text-center text-[13px] text-muted-foreground">
          No skills found matching &quot;{query}&quot;
        </div>
      ) : (
        <div className="mt-1 space-y-0.5">
          {filteredSkills.map((skill, index) => {
            const badgeStyle = CATEGORY_COLORS[skill.category] || "bg-muted text-muted-foreground";
            const isSelected = index === selectedIndex;

            return (
              <button
                key={skill.name}
                type="button"
                onClick={() => onSelectSkill(skill.name)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={cn(
                  "group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-[13px] transition-all",
                  isSelected
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-foreground hover:bg-muted/70",
                )}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="min-w-0 truncate">
                    <span className="font-semibold text-foreground group-hover:text-primary">
                      {skill.name}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 ml-2">
                  <span
                    className={cn(
                      "rounded border px-1.5 py-0.5 text-[10px] font-medium",
                      badgeStyle,
                    )}
                  >
                    {skill.category}
                  </span>
                  <ArrowRight
                    size={14}
                    className={cn(
                      "transition-transform",
                      isSelected
                        ? "translate-x-0.5 text-primary opacity-100"
                        : "opacity-0 group-hover:opacity-100",
                    )}
                  />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
