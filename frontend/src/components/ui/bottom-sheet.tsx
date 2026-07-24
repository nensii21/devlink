"use client";

import * as React from "react";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import { Drawer, DrawerContent, DrawerTitle, DrawerDescription } from "@/components/ui/drawer";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export interface BottomSheetProps {
  /** Whether the bottom sheet is open. */
  open: boolean;
  /** Callback fired when the open state changes. */
  onOpenChange: (open: boolean) => void;
  /** Optional title displayed in the header. */
  title?: string;
  /** Optional description displayed below the title. */
  description?: string;
  /** Optional footer content rendered at the bottom of the sheet. */
  footer?: React.ReactNode;
  /** The content of the bottom sheet. */
  children: React.ReactNode;
  /** Additional CSS classes for the content element. */
  className?: string;
}

export function BottomSheet({
  open,
  onOpenChange,
  title,
  description,
  footer,
  children,
  className,
}: BottomSheetProps) {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerContent className={cn("max-h-[85vh]", className)}>
          <div className="flex shrink-0 items-start justify-between px-4 pt-4 pb-2">
            <div className="min-w-0 flex-1">
              {title && <DrawerTitle className="text-left">{title}</DrawerTitle>}
              {description && (
                <DrawerDescription className="text-left">{description}</DrawerDescription>
              )}
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="ml-4 mt-0.5 shrink-0 cursor-pointer rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4">{children}</div>
          {footer && (
            <div className="shrink-0 px-4 pt-2 pb-[calc(1rem+env(safe-area-inset-bottom))]">
              {footer}
            </div>
          )}
          {!footer && <div className="pb-[env(safe-area-inset-bottom)]" />}
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("sm:max-w-lg", className)}>
        <DialogHeader>
          {title && <DialogTitle>{title}</DialogTitle>}
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        <div className="max-h-[60vh] overflow-y-auto">{children}</div>
        {footer && <DialogFooter>{footer}</DialogFooter>}
      </DialogContent>
    </Dialog>
  );
}
