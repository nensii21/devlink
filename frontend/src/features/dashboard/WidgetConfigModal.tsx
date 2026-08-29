import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  LayoutGrid,
  Pin,
  PinOff,
  RotateCcw,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  WIDGET_REGISTRY,
  type WidgetDefinition,
} from "./dashboardWidgets";
import type { DashboardWidgetLayout } from "@/api/modules/dashboardLayout";
import { TypoCard, TypoCaption } from "@/components/shared/Typography";

export interface WidgetConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  layouts: DashboardWidgetLayout[];
  onToggleVisibility: (id: string) => void;
  onTogglePin: (id: string) => void;
  onReset: () => void;
}

export function WidgetConfigModal({
  open,
  onOpenChange,
  layouts,
  onToggleVisibility,
  onTogglePin,
  onReset,
}: WidgetConfigModalProps) {
  const layoutMap = new Map(layouts.map((l) => [l.id, l]));

  const allWidgets: Array<{
    definition: WidgetDefinition;
    layout: DashboardWidgetLayout;
  }> = Object.values(WIDGET_REGISTRY).map((def) => {
    const layout = layoutMap.get(def.id) || {
      id: def.id,
      order: def.defaultOrder,
      pinned: def.defaultPinned,
      visible: def.defaultVisible,
      column: def.defaultColumn,
    };
    return { definition: def, layout };
  });

  const visibleCount = allWidgets.filter((w) => w.layout.visible).length;
  const pinnedCount = allWidgets.filter((w) => w.layout.pinned).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[85vh] flex flex-col p-6 overflow-hidden">
        <DialogHeader className="pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-lg font-bold flex items-center gap-2 text-foreground">
              <LayoutGrid className="h-5 w-5 text-primary" />
              Customize Widgets
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-muted-foreground">
            Toggle visibility, pin essential sections to the top, or reset to default.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between py-2 px-3 bg-muted/40 rounded-lg text-xs text-muted-foreground">
          <div className="flex gap-4">
            <TypoCaption as="span">
              <strong className="text-foreground">{visibleCount}</strong> visible
            </TypoCaption>
            <TypoCaption as="span">
              <strong className="text-foreground">{pinnedCount}</strong> pinned
            </TypoCaption>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1 cursor-pointer"
          >
            <RotateCcw size={12} /> Reset to Default
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 py-3 pr-1">
          {allWidgets.map(({ definition, layout }) => {
            const Icon = definition.icon;
            return (
              <div
                key={definition.id}
                className={cn(
                  "flex items-center justify-between gap-3 p-3.5 rounded-xl border transition-colors",
                  layout.visible
                    ? "bg-card border-border hover:border-primary/40 shadow-2xs"
                    : "bg-muted/20 border-border/40 opacity-60",
                )}
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="flex items-center justify-center h-9 w-9 rounded-lg bg-primary/10 text-primary shrink-0">
                    <Icon size={18} />
                  </div>
                  <div className="min-w-0">
                    <TypoCard as="p" className="font-semibold text-xs text-foreground flex items-center gap-2 truncate">
                      {definition.title}
                      {layout.pinned && (
                        <TypoCaption as="span" className="text-[10px] bg-primary/15 text-primary px-1.5 py-0.2 rounded font-bold">
                          Pinned
                        </TypoCaption>
                      )}
                    </TypoCard>
                    <TypoCaption as="p" className="text-[11px] text-muted-foreground line-clamp-1 mt-0.5">
                      {definition.description}
                    </TypoCaption>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {/* Pin Toggle */}
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => onTogglePin(definition.id)}
                    className={cn(
                      "h-8 px-2.5 text-xs gap-1.5 cursor-pointer",
                      layout.pinned
                        ? "bg-primary/15 text-primary hover:bg-primary/25"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                    title={layout.pinned ? "Unpin widget" : "Pin widget to top"}
                  >
                    {layout.pinned ? <PinOff size={13} /> : <Pin size={13} />}
                    <span className="hidden sm:inline">
                      {layout.pinned ? "Pinned" : "Pin"}
                    </span>
                  </Button>

                  {/* Visibility Switch */}
                  <div className="flex items-center gap-1.5 pl-2 border-l border-border/60">
                    <Switch
                      checked={layout.visible}
                      onCheckedChange={() => onToggleVisibility(definition.id)}
                      aria-label={`Toggle ${definition.title} visibility`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-border flex justify-end">
          <Button
            type="button"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="gap-1.5 font-semibold"
          >
            <Check size={14} /> Done
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
