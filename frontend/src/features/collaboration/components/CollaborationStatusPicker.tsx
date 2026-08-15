import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import {
  COLLABORATION_STATUSES,
  getCollaborationStatusOption,
  type CollaborationStatus,
} from "@/features/collaboration/types";

interface CollaborationStatusPickerProps {
  value: CollaborationStatus | string;
  onChange: (status: CollaborationStatus) => void;
  disabled?: boolean;
  className?: string;
}

export function CollaborationStatusPicker({
  value,
  onChange,
  disabled = false,
  className,
}: CollaborationStatusPickerProps) {
  const [open, setOpen] = useState(false);
  const current = getCollaborationStatusOption(value);
  const Icon = current.icon;

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className={cn("gap-2", className)} disabled={disabled}>
          <span className={cn("size-2 rounded-full", current.dotClass)} aria-hidden="true" />
          {current.label}
          <ChevronDown className="size-3.5 opacity-60" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Set collaboration status</DropdownMenuLabel>
        <DropdownMenuRadioGroup
          value={value}
          onValueChange={(v) => onChange(v as CollaborationStatus)}
        >
          {COLLABORATION_STATUSES.map((option) => {
            const OptionIcon = option.icon;
            return (
              <DropdownMenuRadioItem key={option.value} value={option.value} className="gap-2 py-2">
                <span className={cn("size-2 rounded-full", option.dotClass)} aria-hidden="true" />
                <OptionIcon className="size-4 text-muted-foreground" aria-hidden="true" />
                <span className="flex flex-col">
                  <span className="text-sm font-medium">{option.label}</span>
                  <span className="text-xs text-muted-foreground">{option.description}</span>
                </span>
                {value === option.value && <Check className="ml-auto size-4" aria-hidden="true" />}
              </DropdownMenuRadioItem>
            );
          })}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
