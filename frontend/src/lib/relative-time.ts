import { formatDistanceToNowStrict, format, isToday, isYesterday } from "date-fns";

/**
 * Format an ISO timestamp into a human-friendly relative string.
 *
 * - "Active now"        — less than 2 minutes ago
 * - "Last active Xm"    — minutes ago
 * - "Last active Xh"    — hours ago
 * - "Last active yesterday" — yesterday
 * - "Last active Xd"    — days ago
 * - "Last active on Mon" — within the current year
 * - "Never active"       — no timestamp provided
 */
export function formatLastActive(iso: string | null | undefined): {
  label: string;
  exact: string | null;
} {
  if (!iso) {
    return { label: "Never active", exact: null };
  }

  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);

  // "Active now" — within the last 2 minutes
  if (diffMin < 2) {
    return { label: "Active now", exact: format(date, "PPpp") };
  }

  // Less than 1 hour — show minutes
  if (diffMin < 60) {
    const dist = formatDistanceToNowStrict(date, { addSuffix: false });
    return {
      label: `Last active ${dist.replace(/\sseconds?\b/, "<1m").replace(/\sminutes?/, "m")}`,
      exact: format(date, "PPpp"),
    };
  }

  // Today — show hours
  if (isToday(date)) {
    const hours = Math.floor(diffMin / 60);
    return {
      label: `Last active ${hours}h ago`,
      exact: format(date, "PPpp"),
    };
  }

  // Yesterday
  if (isYesterday(date)) {
    return {
      label: "Last active yesterday",
      exact: format(date, "PPpp"),
    };
  }

  // Within the current year — show month and day
  if (date.getFullYear() === now.getFullYear()) {
    return {
      label: `Last active on ${format(date, "MMM d")}`,
      exact: format(date, "PPpp"),
    };
  }

  // Older than current year
  const dist = formatDistanceToNowStrict(date, { addSuffix: false });
  return {
    label: `Last active ${dist} ago`,
    exact: format(date, "PPpp"),
  };
}
