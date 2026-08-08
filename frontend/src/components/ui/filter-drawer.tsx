// @ts-nocheck
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
  type?: "multi" | "single" | "select" | "range" | "search";
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
  /** Drawer slide direction for desktop/tablet sheet */
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
  };

  const handleTextChange = (sectionId: string, text: string | number) => {
    setDraftValues((prev) => ({ ...prev, [sectionId]: text }));
  };

  const handleApply = () => {
    onApply(draftValues);
    onOpenChange(false);
  };

  const handleReset = () => {
    onReset();
    setDraftValues({});
    onOpenChange(false);
  };

  const renderSectionContent = (section: FilterSection) => {
    const type = section.type || "multi";

    if (type === "search") {
      return (
        <div className="relative mt-2">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="text"
            value={asText(draftValues[section.id])}
            onChange={(e) => handleTextChange(section.id, e.target.value)}
            placeholder={section.placeholder || `Search ${section.title.toLowerCase()}...`}
            className="w-full rounded-md border border-border bg-surface py-1.5 pl-8 pr-3 text-[13px] text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            aria-label={section.title}
          />
        </div>
      );
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

    // Default multi or single checkbox/radio chip buttons
    const isMulti = type === "multi";
    const selectedList = asList(draftValues[section.id]);
    const selectedText = asText(draftValues[section.id]);

    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {section.options?.map((option) => {
          const isSelected = isMulti
            ? selectedList.includes(option.value)
            : selectedText === option.value;

          return (
            <button
              key={option.value}
              type="button"
              onClick={() => handleOptionToggle(section.id, option.value, isMulti)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-medium transition-all focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer",
                isSelected
                  ? "border-primary bg-primary/10 text-primary font-semibold"
                  : "border-border bg-surface text-muted-foreground hover:border-foreground/30 hover:text-foreground",
              )}
              aria-pressed={isSelected}
              aria-label={`${section.title}: ${option.label}`}
            >
              {isSelected && <Check size={12} className="shrink-0" />}
              <span>{option.label}</span>
              {option.count !== undefined && (
                <span className="ml-1 text-[10px] opacity-70">({option.count})</span>
              )}
            </button>
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
          <h4 className="text-[13px] font-semibold text-foreground uppercase tracking-wider">
            {section.title}
          </h4>
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
