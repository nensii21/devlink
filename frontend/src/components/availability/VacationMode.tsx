import React from "react";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";

interface Props {
  mode: boolean;
  start: string | null;
  end: string | null;
  onChangeMode: (mode: boolean) => void;
  onChangeStart: (start: string | null) => void;
  onChangeEnd: (end: string | null) => void;
}

export const VacationMode: React.FC<Props> = ({
  mode,
  start,
  end,
  onChangeMode,
  onChangeStart,
  onChangeEnd,
}) => {
  return (
    <div className="space-y-4 max-w-sm">
      <div className="flex items-center justify-between">
        <div>
          <Label className="mb-1 block">Vacation Mode</Label>
          <p className="text-xs text-surface-500">Temporarily block all incoming requests.</p>
        </div>
        <Switch checked={mode} onCheckedChange={onChangeMode} />
      </div>

      {mode && (
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div>
            <Label className="mb-2 block text-xs">Start Date (Optional)</Label>
            <input
              type="date"
              value={start || ""}
              onChange={(e) => onChangeStart(e.target.value || null)}
              className="w-full bg-surface-50 border border-surface-200 rounded-md px-3 py-1.5 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            />
          </div>
          <div>
            <Label className="mb-2 block text-xs">End Date (Optional)</Label>
            <input
              type="date"
              value={end || ""}
              onChange={(e) => onChangeEnd(e.target.value || null)}
              className="w-full bg-surface-50 border border-surface-200 rounded-md px-3 py-1.5 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            />
          </div>
        </div>
      )}
    </div>
  );
};
