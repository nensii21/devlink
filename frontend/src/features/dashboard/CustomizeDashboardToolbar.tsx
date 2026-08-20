import React from "react";
import {
  SlidersHorizontal,
  Plus,
  RotateCcw,
  Check,
  Eye,
  GripVertical,
  Pin,
  Save,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export interface CustomizeDashboardToolbarProps {
  isCustomizing: boolean;
  isSaving: boolean;
  hiddenCount: number;
  onToggleCustomizing: () => void;
  onOpenAddModal: () => void;
  onResetLayout: () => void;
  onSaveLayout: () => void;
}

export function CustomizeDashboardToolbar({
  isCustomizing,
  isSaving,
  hiddenCount,
  onToggleCustomizing,
  onOpenAddModal,
  onResetLayout,
  onSaveLayout,
}: CustomizeDashboardToolbarProps) {
  if (!isCustomizing) {
    return (
      <div className="flex items-center justify-end">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onToggleCustomizing}
          className="gap-2 text-xs font-semibold h-8 bg-card border-border hover:bg-muted cursor-pointer"
        >
          <SlidersHorizontal size={13} />
          Customize Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="sticky top-16 z-40 p-4 rounded-2xl border border-primary/30 bg-primary/10 backdrop-blur-md shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-primary text-primary-foreground shrink-0 shadow-xs">
          <GripVertical size={16} />
        </div>
        <div>
          <p className="text-xs font-bold text-foreground flex items-center gap-2">
            Customizing Dashboard Layout
            <span className="text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-semibold">
              Live Edit
            </span>
          </p>
          <p className="text-[11px] text-muted-foreground">
            Drag widgets to reorder, pin to freeze at top, or hide widgets you don't need.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 shrink-0">
        {/* Manage / Restore Widgets */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onOpenAddModal}
          className="h-8 text-xs gap-1.5 bg-card border-border hover:bg-muted cursor-pointer"
        >
          <Plus size={13} /> Manage Widgets
          {hiddenCount > 0 && (
            <span className="ml-0.5 text-[10px] font-bold bg-muted-foreground/20 px-1.5 py-0.2 rounded-full">
              {hiddenCount} hidden
            </span>
          )}
        </Button>

        {/* Reset to Default */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onResetLayout}
          className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-foreground cursor-pointer"
        >
          <RotateCcw size={13} /> Reset Layout
        </Button>

        {/* Save & Finish */}
        <Button
          type="button"
          size="sm"
          onClick={onSaveLayout}
          disabled={isSaving}
          className="h-8 text-xs gap-1.5 font-bold shadow-xs cursor-pointer"
        >
          {isSaving ? (
            <>
              <Loader2 size={13} className="animate-spin" /> Saving...
            </>
          ) : (
            <>
              <Check size={13} /> Save Layout
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
