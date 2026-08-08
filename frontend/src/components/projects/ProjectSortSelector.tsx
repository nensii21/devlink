import React from "react";
import {
  ArrowUpDown,
  Sparkles,
  Clock,
  Calendar,
  Flame,
  Bookmark,
  Users2,
  RefreshCw,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type SortOption =
  | "newest"
  | "oldest"
  | "most_active"
  | "most_bookmarked"
  | "most_applications"
  | "recently_updated"
  | "ai_match_score";

export interface ProjectSortSelectorProps {
  currentSort?: SortOption | string;
  onSortChange: (sort: SortOption) => void;
  isLoading?: boolean;
}

export const SORT_OPTIONS: { value: SortOption; label: string; icon: React.ElementType }[] = [
  { value: "newest", label: "Newest", icon: Clock },
  { value: "oldest", label: "Oldest", icon: Calendar },
  { value: "most_active", label: "Most Active", icon: Flame },
  { value: "most_bookmarked", label: "Most Bookmarked", icon: Bookmark },
  { value: "most_applications", label: "Most Applications", icon: Users2 },
  { value: "recently_updated", label: "Recently Updated", icon: RefreshCw },
  { value: "ai_match_score", label: "AI Match Score", icon: Sparkles },
];

export const ProjectSortSelector: React.FC<ProjectSortSelectorProps> = ({
  currentSort = "newest",
  onSortChange,
  isLoading = false,
}) => {
  return (
    <div className="flex items-center gap-2 w-full sm:w-auto">
      <Select
        value={currentSort as string}
        onValueChange={(val) => onSortChange(val as SortOption)}
        disabled={isLoading}
      >
        <SelectTrigger className="w-full sm:w-[200px] h-9 text-xs font-medium border-border/80 bg-background hover:bg-accent/50 focus:ring-1 focus:ring-ring transition-colors">
          <div className="flex items-center gap-2 truncate">
            <ArrowUpDown
              className={`h-3.5 w-3.5 text-muted-foreground ${isLoading ? "animate-spin" : ""}`}
            />
            <span className="truncate">
              {SORT_OPTIONS.find((opt) => opt.value === currentSort)?.label || "Sort Projects"}
            </span>
          </div>
        </SelectTrigger>
        <SelectContent align="end" className="w-[220px]">
          {SORT_OPTIONS.map((opt) => {
            const IconComp = opt.icon;
            return (
              <SelectItem
                key={opt.value}
                value={opt.value}
                className="text-xs flex items-center gap-2 cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <IconComp className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>{opt.label}</span>
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
};
