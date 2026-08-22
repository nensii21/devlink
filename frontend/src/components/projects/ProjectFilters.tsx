import { useProjectFilters } from "@/hooks/useProjectFilters";
import { X, Check, ChevronsUpDown, Bookmark } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { TypoSection, TypoCard } from "@/components/shared/Typography";
import { useSavedSearches } from "@/stores/useSavedSearches";
import { SaveSearchDialog } from "@/components/shared/SaveSearchDialog";

const LANGUAGES = [
  "JavaScript",
  "TypeScript",
  "Python",
  "Java",
  "Go",
  "Rust",
  "C++",
  "C#",
  "Ruby",
  "PHP",
];
const EXPERIENCES = ["Beginner", "Intermediate", "Advanced"];
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
  "Vue.js",
  "Angular",
  "Svelte",
  "Tailwind CSS",
  "React Native",
  "Flutter",
  "Swift",
  "Kotlin",
];

export function ProjectFilters() {
  const { filters, setFilters, clearFilters, hasActiveFilters } = useProjectFilters();

  const handleLanguageChange = (lang: string, checked: boolean) => {
    const current = filters.language || [];
    const next = checked ? [...current, lang] : current.filter((l: string) => l !== lang);
    setFilters({ language: next });
  };

  const handleExperienceChange = (exp: string, checked: boolean) => {
    const current = filters.experience || [];
    const next = checked ? [...current, exp] : current.filter((e: string) => e !== exp);
    setFilters({ experience: next });
  };

  const handleTechToggle = (tech: string) => {
    const current = filters.tech || [];
    const next = current.includes(tech)
      ? current.filter((t: string) => t !== tech)
      : [...current, tech];
    setFilters({ tech: next });
  };

  const [techOpen, setTechOpen] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const saveSearch = useSavedSearches((s) => s.saveSearch);

  return (
    <div className="rounded-lg border border-border bg-card p-5 my-4 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <TypoSection>Filters</TypoSection>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSaveDialogOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <Bookmark size={14} /> Save Search
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1.5 rounded-md text-[12px] font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <X size={14} /> Clear all
            </button>
          )}
        </div>
      </div>

      <SaveSearchDialog
        open={saveDialogOpen}
        onOpenChange={setSaveDialogOpen}
        onSave={(name) => {
          saveSearch({
            name,
            type: "Projects",
            filters,
            query: filters.q || "",
          } as any);
        }}
      />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Language Filter */}
        <div className="space-y-4">
          <TypoCard>Language</TypoCard>
          <div className="flex flex-col gap-3">
            {LANGUAGES.map((lang) => (
              <div key={lang} className="flex items-center gap-2">
                <Checkbox
                  id={`lang-${lang}`}
                  checked={(filters.language || []).includes(lang)}
                  onCheckedChange={(checked) => handleLanguageChange(lang, !!checked)}
                />
                <label
                  htmlFor={`lang-${lang}`}
                  className="text-[13px] font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {lang}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Experience Filter */}
        <div className="space-y-4">
          <TypoCard>Experience Level</TypoCard>
          <div className="flex flex-col gap-3">
            {EXPERIENCES.map((exp) => (
              <div key={exp} className="flex items-center gap-2">
                <Checkbox
                  id={`exp-${exp}`}
                  checked={(filters.experience || []).includes(exp.toLowerCase())}
                  onCheckedChange={(checked) =>
                    handleExperienceChange(exp.toLowerCase(), !!checked)
                  }
                />
                <label
                  htmlFor={`exp-${exp}`}
                  className="text-[13px] font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {exp}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Filters */}
        <div className="space-y-6">
          <div className="space-y-4">
            <TypoCard>Project Details</TypoCard>

            <div className="flex items-center justify-between">
              <label htmlFor="remote-toggle" className="text-[13px] font-medium cursor-pointer">
                Remote Only
              </label>
              <Switch
                id="remote-toggle"
                checked={filters.remote === true}
                onCheckedChange={(checked) => setFilters({ remote: checked || undefined })}
              />
            </div>

            <div className="flex items-center justify-between">
              <label htmlFor="paid-toggle" className="text-[13px] font-medium cursor-pointer">
                Paid Only
              </label>
              <Switch
                id="paid-toggle"
                checked={filters.paid === true}
                onCheckedChange={(checked) => setFilters({ paid: checked || undefined })}
              />
            </div>

            <div className="flex items-center justify-between">
              <label htmlFor="opensource-toggle" className="text-[13px] font-medium cursor-pointer">
                Open Source Only
              </label>
              <Switch
                id="opensource-toggle"
                checked={filters.opensource === true}
                onCheckedChange={(checked) => setFilters({ opensource: checked || undefined })}
              />
            </div>
          </div>

          <div className="space-y-3">
            <TypoCard>Tech Stack</TypoCard>
            <Popover open={techOpen} onOpenChange={setTechOpen}>
              <PopoverTrigger asChild>
                <button className="flex w-full items-center justify-between rounded-md border border-border bg-surface px-3 py-2 text-[13px] hover:bg-muted">
                  <span className="truncate">
                    {(filters.tech || []).length > 0
                      ? `${(filters.tech || []).length} selected`
                      : "Select tech stack..."}
                  </span>
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-[200px] p-0" align="start">
                <Command>
                  <CommandInput placeholder="Search tech..." />
                  <CommandList>
                    <CommandEmpty>No tech found.</CommandEmpty>
                    <CommandGroup>
                      {TECH_STACKS.map((tech) => {
                        const isSelected = (filters.tech || []).includes(tech);
                        return (
                          <CommandItem key={tech} onSelect={() => handleTechToggle(tech)}>
                            <div
                              className={cn(
                                "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                                isSelected
                                  ? "bg-primary text-primary-foreground"
                                  : "opacity-50 [&_svg]:invisible",
                              )}
                            >
                              <Check className={cn("h-3 w-3")} />
                            </div>
                            {tech}
                          </CommandItem>
                        );
                      })}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            <div className="flex flex-wrap gap-1">
              {(filters.tech || []).map((t: string) => (
                <Badge
                  key={t}
                  variant="secondary"
                  className="px-1.5 py-0 text-[11px] font-normal cursor-pointer flex items-center gap-1"
                  onClick={() => handleTechToggle(t)}
                >
                  {t}
                  <X className="h-3 w-3" />
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
