import React from "react";
import { WorkingHours as IWorkingHours, TimeSlot, DAYS_OF_WEEK } from "../../types/availability";
import { Switch } from "../ui/switch";
import { Plus, Trash2 } from "lucide-react";

interface Props {
  value: IWorkingHours;
  onChange: (value: IWorkingHours) => void;
}

const DEFAULT_SLOT = { start: "09:00", end: "17:00" };

export const WorkingHours: React.FC<Props> = ({ value, onChange }) => {
  const handleToggleDay = (day: string, enabled: boolean) => {
    const newValue = { ...value };
    if (enabled) {
      newValue[day] = [DEFAULT_SLOT];
    } else {
      newValue[day] = [];
    }
    onChange(newValue);
  };

  const handleUpdateSlot = (day: string, index: number, field: "start" | "end", time: string) => {
    const newValue = { ...value };
    newValue[day][index] = { ...newValue[day][index], [field]: time };
    onChange(newValue);
  };

  const handleAddSlot = (day: string) => {
    const newValue = { ...value };
    newValue[day] = [...(newValue[day] || []), { start: "09:00", end: "17:00" }];
    onChange(newValue);
  };

  const handleRemoveSlot = (day: string, index: number) => {
    const newValue = { ...value };
    newValue[day].splice(index, 1);
    onChange(newValue);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-surface-900 mb-1">Working Hours</h3>
        <p className="text-xs text-surface-500 mb-4">Set your weekly availability schedule.</p>
      </div>

      <div className="space-y-4">
        {DAYS_OF_WEEK.map((day) => {
          const slots = value[day] || [];
          const isEnabled = slots.length > 0;

          return (
            <div key={day} className="flex flex-col sm:flex-row sm:items-start gap-4">
              <div className="flex items-center gap-3 w-40 shrink-0 h-10">
                <Switch checked={isEnabled} onCheckedChange={(c) => handleToggleDay(day, c)} />
                <span className="text-sm font-medium capitalize text-surface-700">{day}</span>
              </div>

              <div className="flex-1 flex flex-col gap-2">
                {!isEnabled && (
                  <div className="h-10 flex items-center text-sm text-surface-400">Unavailable</div>
                )}

                {isEnabled &&
                  slots.map((slot, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <input
                        type="time"
                        value={slot.start}
                        onChange={(e) => handleUpdateSlot(day, idx, "start", e.target.value)}
                        className="bg-surface-50 border border-surface-200 rounded-md px-3 py-1.5 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                      />
                      <span className="text-surface-400">-</span>
                      <input
                        type="time"
                        value={slot.end}
                        onChange={(e) => handleUpdateSlot(day, idx, "end", e.target.value)}
                        className="bg-surface-50 border border-surface-200 rounded-md px-3 py-1.5 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                      />

                      <button
                        onClick={() => handleRemoveSlot(day, idx)}
                        className="p-2 text-surface-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}

                {isEnabled && (
                  <button
                    onClick={() => handleAddSlot(day)}
                    className="flex items-center gap-1.5 text-sm text-primary-600 font-medium hover:text-primary-700 w-max"
                  >
                    <Plus className="w-4 h-4" /> Add time
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
