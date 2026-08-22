import React from "react";
import { Label } from "../ui/label";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Kolkata",
  "Asia/Tokyo",
  "Australia/Sydney",
];

export const TimezoneSelector: React.FC<Props> = ({ value, onChange }) => {
  return (
    <div className="max-w-xs">
      <Label className="mb-2 block">Timezone</Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-surface-50 border border-surface-200 rounded-md px-3 py-2 text-sm outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
      >
        {COMMON_TIMEZONES.map((tz) => (
          <option key={tz} value={tz}>
            {tz}
          </option>
        ))}
      </select>
      <p className="text-xs text-surface-400 mt-2">All times will be displayed in this timezone.</p>
    </div>
  );
};
