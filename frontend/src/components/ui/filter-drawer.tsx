"use client";

import * as React from "react";
import { X, RotateCcw, Filter, Check, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
} from "@/components/ui/drawer";
import { useIsMobile } from "@/hooks/use-mobile";
import { TypoCard } from "@/components/shared/Typography";

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

/**
 * What a single section can hold.
 *
 * `multi` sections store a string array, `single`/`select`/`search` store a
 * string, and `range` stores a number. This was previously typed as `unknown`,
 * which pushed the burden onto every render branch below — each of which then
 * handed an `unknown` straight to a DOM input and failed to compile.
 */
export type FilterValue = string | number | string[] | undefined;

export type FilterValues = Record<string, FilterValue>;

/** Narrow a stored value for a text input or a chip comparison. */
function asText(value: FilterValue): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return "";
}

/** Narrow a stored value for a multi-select section. */
function asList(value: FilterValue): string[] {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value !== "") return [value];
  return [];
}

/** Narrow a stored value for a range input, falling back to the minimum. */
function asNumber(value: FilterValue, fallback: number): number {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return fallback;
}

export interface FilterSection {
  id: string;
  title: string;
  type?: "multi" | "multi-select" | "single" | "select" | "range" | "search" | "chip";
  options?: FilterOption[];
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
}

export interface FilterDrawerProps {
  /** Whether the filter drawer is open */
  open: boolean;
  /** Callback when open state changes */
  onOpenChange: (open: boolean) => void;
  /** Custom title for the filter drawer */
  title?: string;
  /** Optional subtitle or description */
  description?: string;
  /** Configurable filter sections list */
  sections: FilterSection[];
  /** Current state of filter values keyed by section ID */
  values: FilterValues;
  /** Callback fired when user clicks Apply Filters */
  onApply: (newValues: FilterValues) => void;
  /** Callback fired when user clicks Reset Filters */
  onReset: () => void;
  /** Number of active filters to display in badge */
  activeCount?: number;
  /** Drawer slide direction for desktop, tablet sheet */
  side?: "right" | "left";
  /** Optional custom CSS classes */
  className?: string;
}

export function FilterDrawer({
  open,
  onOpenChange,
  title = "Filters",
  description = "Refine search and filter options",
  sections,
  values,
  onApply,
  onReset,
  activeCount = 0,
  side = "right",
  className,
}: FilterDrawerProps) {
  const isMobile = useIsMobile();
  const [draftValues, setDraftValues] = React.useState<FilterValues>(values);

  // Sync draft state with values when drawer opens
  React.useEffect(() => {
    if (open) {
      setDraftValues(values);
    }
  }, [open, values]);

  // Handle ESC key for keyboard accessibility
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  // Track search queries per section for pills display
  const [searchQueries, setSearchQueries] = React.useState<Record<string, string>>(() =>
    Object.fromEntries(sections.map((s) => [s.id, ""])),
  );

  // Update search query state
  const updateSearchQuery = (sectionId: string, query: string) => {
    setSearchQueries((prev) => ({ ...prev, [sectionId]: query }));
  };

  // Handle option toggle (checkbox/radio/chip)
  const handleOptionToggle = (sectionId: string, optionValue: string, isMulti = true) => {
    setDraftValues((prev) => {
      if (isMulti) {
        const current = asList(prev[sectionId]);
        const exists = current.includes(optionValue);
        const updated = exists
          ? current.filter((v) => v !== optionValue)
          : [...current, optionValue];
        return { ...prev, [sectionId]: updated };
      }
      return { ...prev, [sectionId]: optionValue === prev[sectionId] ? "" : optionValue };
    });
    // Also update search query for pills display
    if (!isMulti) {
      updateSearchQuery(sectionId, optionValue);
    }
  };

  // Handle text input change (for search and single select)
  const handleTextChange = (sectionId: string, text: string | number) => {
    setDraftValues((prev) => ({ ...prev, [sectionId]: text }));
    updateSearchQuery(sectionId, typeof text === "string" ? text : "");
  };

  const handleApply = () => {
    onApply(draftValues);
    onOpenChange(false);
  };

  const handleReset = () => {
    onReset();
    setDraftValues({});
    setSearchQueries(Object.fromEntries(sections.map((s) => [s.id, ""])));
    onOpenChange(false);
  };

  const renderPill = (
    sectionId: string,
    optionValue: string,
    label: string,
    isSelected: boolean,
    hasSearchQuery: boolean,

  ) => {
    const section = sections.find((s) => s.id === sectionId);
    const isSearchMode = section?.type === "search";
    const isMulti =
      section?.type === "multi" || section?.type === "multi-select" || section?.type === "chip";

    return (
      <button
        key={optionValue}
        type="button"
        onClick={() => handleOptionToggle(sectionId, optionValue, isMulti)}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-medium transition-all focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer",
          isSelected
            ? "border-primary bg-primary/10 text-primary font-semibold"
            : "border-border bg-surface text-muted-foreground hover:border-foreground/30 hover:text-foreground",
          // Show pill as "active search" when there's a search query
          isSearchMode && isSelected
            ? "border-primary bg-primary/10 text-primary font-semibold"
            : "",
        )}
        aria-pressed={isSelected}
        aria-label={`${sectionId}: ${optionLabel(sectionId, optionValue)}`}
      >
        {isSelected && <Check size={12} className="shrink-0" />}
        <span>{label}</span>
        {hasSearchQuery && <span className="ml-1 text-[10px] opacity-70">🔍 active</span>}
      </button>
    );
  };

  // Get option label for aria
  const optionLabel = (sectionId: string, value: string) => {
    const section = sections.find((s) => s.id === sectionId);
    const option = section?.options?.find((opt) => opt.value === value);
    return option ? option.label : value;
  };

  // Render search input with pill
  const renderSearchInput = (section: FilterSection) => {
    const hasQuery = Boolean(searchQueries[section.id] && searchQueries[section.id].trim());

    return (
      <div className="relative mt-2 flex items-center">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          type="text"
          value={asText(draftValues[section.id])}
          onChange={(e) => {
            const query = e.target.value.trim();
            handleTextChange(section.id, query);
          }}
          placeholder={section.placeholder || `Search ${section.title.toLowerCase()}...`}
          className="w-full rounded-md border border-border bg-surface py-1.5 pl-8 pr-3 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          aria-label={section.title}
        />
        {hasQuery && (
          <button
            type="button"
            onClick={() => {
              handleTextChange(section.id, "");
              setSearchQueries((prev) => ({ ...prev, [section.id]: "" }));
            }}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-accent/20 cursor-pointer"
            aria-label="Clear search"
          >
            <X size={14} className="text-muted-foreground" />
          </button>
        )}
      </div>
    );
  };

  // Render filter section with pills and search
  const renderSectionContent = (section: FilterSection) => {
    const type = section.type || "multi";

    // For search type, render search input with pill
    if (type === "search") {
      return renderSearchInput(section);
    }

    if (type === "select") {
      return (
        <select
          value={asText(draftValues[section.id])}
          onChange={(e) => handleTextChange(section.id, e.target.value)}
          className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-1.5 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          aria-label={section.title}
        >
          <option value="">All</option>
          {section.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label} {opt.count !== undefined ? `(${opt.count})` : ""}
            </option>
          ))}
        </select>
      );
    }

    if (type === "range") {
      const min = section.min ?? 0;
      const max = section.max ?? 100;
      const step = section.step ?? 1;
      const val = asNumber(draftValues[section.id], min);

      return (
        <div className="mt-2 space-y-2">
          <div className="flex items-center justify-between text-[12px] text-muted-foreground">
            <span>{min}</span>
            <span className="font-semibold text-foreground">{val}</span>
            <span>{max}</span>
          </div>
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={val}
            onChange={(e) => handleTextChange(section.id, Number(e.target.value))}
            className="w-full cursor-pointer accent-primary"
            aria-label={section.title}
          />
        </div>
      );
    }

    // Default multi or single - render chips/buttons
    const isMulti = type === "multi" || type === "multi-select" || type === "chip";
    const selectedList = asList(draftValues[section.id]);
    const selectedText = asText(draftValues[section.id]);

    // Get search query for this section
    const sectionSearchQuery = searchQueries[section.id] || "";

    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {section.options?.map((option) => {
          const isSelected = isMulti
            ? selectedList.includes(option.value)
            : selectedText === option.value;

          return renderPill(
            section.id,
            option.value,
            option.label,
            isSelected,
            sectionSearchQuery !== "",

          );
        })}
      </div>
    );
  };

  const bodyContent = (
    <div className="flex flex-col h-full space-y-6 overflow-y-auto pr-1 py-2">
      {sections.map((section) => (
        <div
          key={section.id}
          className="space-y-1.5 border-b border-border/50 pb-4 last:border-b-0 last:pb-0"
        >
          <TypoCard>{section.title}</TypoCard>
          {renderSectionContent(section)}
        </div>
      ))}
    </div>
  );

  const footerActions = (
    <div className="flex items-center justify-between gap-3 pt-4 border-t border-border mt-auto">
      <button
        type="button"
        onClick={handleReset}
        className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-[13px] font-medium text-muted-foreground hover:border-destructive/40 hover:text-destructive transition-colors cursor-pointer"
        aria-label="Reset all filters"
      >
        <RotateCcw size={13} />
        Reset
      </button>
      <button
        type="button"
        onClick={handleApply}
        className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-md bg-primary px-4 py-2 text-[13px] font-semibold text-primary-foreground hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
        aria-label="Apply filters"
      >
        Apply Filters
      </button>
    </div>
  );

  // Check if any section has active search query
  const hasAnySearchQuery = React.useMemo(() => {
    return Object.values(searchQueries).some((q) => q && q.trim());
  }, [searchQueries]);

  // Check if there are any filters active (selected chips or search queries)
  const hasActiveFilters = React.useMemo(() => {
    // Check if any multi/select section has selected values
    const hasSelected = sections.some((section) => {
      const isMulti = section.type !== "select" && section.type !== "range";
      const selectedList = asList(draftValues[section.id]);
      return selectedList.length > 0;
    });
    return hasSelected || hasAnySearchQuery;
  }, [sections, draftValues, hasAnySearchQuery]);

  if (!hasActiveFilters && !open) {
    // Show empty state when no filters are active and drawer is closed
    return null;
  }

  if (isMobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerContent
          className={cn("max-h-[85vh] p-4 flex flex-col", className)}
          role="dialog"
          aria-modal="true"
        >
          <DrawerHeader className="px-0 pb-2 text-left">
            <div className="flex items-center justify-between">
              <DrawerTitle className="text-lg font-bold flex items-center gap-2">
                <Filter size={18} className="text-primary" />
                {title}
                {activeCount > 0 && (
                  <span className="grid h-5 w-5 place-items-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                    {activeCount}
                  </span>
                )}
              </DrawerTitle>
              <button
                onClick={() => onOpenChange(false)}
                className="rounded-sm opacity-70 hover:opacity-100 p-1 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Close filters"
              >
                <X size={16} />
              </button>
            </div>
            {description && (
              <DrawerDescription className="text-xs">{description}</DrawerDescription>
            )}
          </DrawerHeader>

          <div className="flex-1 min-h-0 overflow-y-auto">{bodyContent}</div>

          {footerActions}
        </DrawerContent>
      </Drawer>
    );
  }


  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side={side}
        className={cn("w-full sm:max-w-md flex flex-col p-6", className)}
        role="dialog"
        aria-modal="true"
      >
        <SheetHeader className="px-0 pb-4 text-left border-b border-border">
          <SheetTitle className="text-lg font-bold flex items-center gap-2">
            <Filter size={18} className="text-primary" />
            {title}
            {activeCount > 0 && (
              <span className="grid h-5 w-5 place-items-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                {activeCount}
              </span>
            )}
          </SheetTitle>
          {description && <SheetDescription className="text-xs">{description}</SheetDescription>}
        </SheetHeader>

        <div className="flex-1 min-h-0 overflow-y-auto my-2">{bodyContent}</div>

        {footerActions}
      </SheetContent>
    </Sheet>
  );
}
