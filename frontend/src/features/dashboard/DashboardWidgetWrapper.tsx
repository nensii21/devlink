import React from "react";
import {
  GripVertical,
  Pin,
  PinOff,
  EyeOff,
  ArrowUp,
  ArrowDown,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { WidgetDefinition } from "./dashboardWidgets";

export interface DashboardWidgetWrapperProps {
  widget: WidgetDefinition;
  isCustomizing: boolean;
  isPinned: boolean;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  onPinToggle: (id: string) => void;
  onHide: (id: string) => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  onDragStart?: (e: React.DragEvent, id: string) => void;
  onDragOver?: (e: React.DragEvent, id: string) => void;
  onDrop?: (e: React.DragEvent, id: string) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  isDragging?: boolean;
  isDragOver?: boolean;
  className?: string;
}

export function DashboardWidgetWrapper({
  widget,
  isCustomizing,
  isPinned,
  canMoveUp = true,
  canMoveDown = true,
  onPinToggle,
  onHide,
  onMoveUp,
  onMoveDown,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragging = false,
  isDragOver = false,
  className,
}: DashboardWidgetWrapperProps) {
  const Component = widget.component;

  return (
    <div
      draggable={isCustomizing}
      onDragStart={(e) => isCustomizing && onDragStart?.(e, widget.id)}
      onDragOver={(e) => isCustomizing && onDragOver?.(e, widget.id)}
      onDrop={(e) => isCustomizing && onDrop?.(e, widget.id)}
      onDragEnd={onDragEnd}
      data-widget-id={widget.id}
      className={cn(
        "relative transition-all duration-200 flex flex-col rounded-2xl",
        isCustomizing &&
          "ring-2 ring-dashed ring-primary/40 bg-card/90 hover:ring-primary hover:shadow-md cursor-grab active:cursor-grabbing",
        isDragging && "opacity-40 scale-[0.98] ring-4 ring-primary",
        isDragOver && "ring-4 ring-primary bg-primary/5 scale-[1.01]",
        className,
      )}
    >
      {/* Pinned Badge in Normal Mode */}
      {!isCustomizing && isPinned && (
        <div
          title="Pinned to top"
          className="absolute -top-2.5 -right-2.5 z-20 flex items-center justify-center h-6 w-6 rounded-full bg-primary text-primary-foreground shadow-md"
        >
          <Pin size={12} className="fill-current" />
        </div>
      )}

      {/* Customization Toolbar Header */}
      {isCustomizing && (
        <div className="flex items-center justify-between gap-2 px-4 py-2 bg-muted/80 backdrop-blur-xs border-b border-border/80 rounded-t-2xl z-30">
          <div className="flex items-center gap-2 min-w-0">
            <span
              className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground p-0.5 rounded"
              title="Drag to rearrange"
            >
              <GripVertical size={16} />
            </span>
            <span className="font-semibold text-xs text-foreground truncate">
              {widget.title}
            </span>
            {isPinned && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider bg-primary/15 text-primary border border-primary/25 px-1.5 py-0.5 rounded">
                <Pin size={9} className="fill-current" /> Pinned
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {/* Move Up */}
            <button
              type="button"
              onClick={() => onMoveUp(widget.id)}
              disabled={!canMoveUp}
              className="p-1 rounded text-muted-foreground hover:bg-card hover:text-foreground disabled:opacity-20 cursor-pointer"
              title="Move Up"
            >
              <ArrowUp size={13} />
            </button>

            {/* Move Down */}
            <button
              type="button"
              onClick={() => onMoveDown(widget.id)}
              disabled={!canMoveDown}
              className="p-1 rounded text-muted-foreground hover:bg-card hover:text-foreground disabled:opacity-20 cursor-pointer"
              title="Move Down"
            >
              <ArrowDown size={13} />
            </button>

            {/* Pin Toggle */}
            <button
              type="button"
              onClick={() => onPinToggle(widget.id)}
              className={cn(
                "p-1 rounded transition-colors cursor-pointer",
                isPinned
                  ? "bg-primary/20 text-primary hover:bg-primary/30"
                  : "text-muted-foreground hover:bg-card hover:text-foreground",
              )}
              title={isPinned ? "Unpin widget" : "Pin widget to top"}
            >
              {isPinned ? <PinOff size={13} /> : <Pin size={13} />}
            </button>

            {/* Hide Widget */}
            <button
              type="button"
              onClick={() => onHide(widget.id)}
              className="p-1 rounded text-muted-foreground hover:bg-destructive/15 hover:text-destructive transition-colors cursor-pointer"
              title="Hide widget"
            >
              <EyeOff size={13} />
            </button>
          </div>
        </div>
      )}

      {/* Inner Widget Component */}
      <div className={cn("flex-1", isCustomizing && "pointer-events-none select-none opacity-90")}>
        <Component />
      </div>
    </div>
  );
}
