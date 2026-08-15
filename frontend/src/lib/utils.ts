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

  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase();
  }

  const initials = parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  return initials || fallback;
}

export function sanitizeUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  
  // Basic check for relative URLs
  if (url.startsWith("/")) {
    return url;
  }
  
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch (e) {
    // Invalid URL parsing
  }
  
  return undefined;
}
