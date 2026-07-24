import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getInitials(name?: string | null, fallback = "?") {
  const normalizedName = name?.trim();

  if (!normalizedName) {
    return fallback;
  }

  const parts = normalizedName.split(/\s+/).filter(Boolean);

  if (parts.length === 0) {
    return fallback;
  }

  const initials = parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  return initials || fallback;
}
