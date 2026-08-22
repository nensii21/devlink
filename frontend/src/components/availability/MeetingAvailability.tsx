import React from "react";
import { Label } from "../ui/label";

interface Props {
  value: number;
  onChange: (value: number) => void;
}

const DURATIONS = [15, 30, 45, 60, 90, 120];

export const MeetingAvailability: React.FC<Props> = ({ value, onChange }) => {
  return (
    <div className="max-w-xs">
      <Label className="mb-2 block">Meeting Duration</Label>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full bg-surface-50 border border-surface-200 rounded-md px-3 py-2 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
      >
        {DURATIONS.map((dur) => (
          <option key={dur} value={dur}>
            {dur} minutes
          </option>
        ))}
      </select>
      <p className="text-xs text-surface-400 mt-2">How long a typical meeting slot should be.</p>
    </div>
  );
};
