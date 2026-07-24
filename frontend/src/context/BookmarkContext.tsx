import { createContext, useContext, useState, useCallback, useEffect } from "react";
import type { ReactNode } from "react";
import { builders } from "@/mocks/seed";

export interface BookmarkDeveloper {
  id: string | null;
  name: string;
  role: string;
  avatar_url: string | null;
  location?: string;
  experience?: string;
  skills?: string[];
}

interface BookmarkContextValue {
  bookmarkedDevs: BookmarkDeveloper[];
  toggleBookmark: (dev: BookmarkDeveloper) => void;
}

const STORAGE_KEY = "devlink-bookmarked-devs";

function loadBookmarked(): BookmarkDeveloper[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch {
    // ignore
  }
  return [];
}

function saveBookmarked(devs: BookmarkDeveloper[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(devs));
}

const BookmarkContext = createContext<BookmarkContextValue | null>(null);

export function BookmarkProvider({ children }: { children: ReactNode }) {
  const [bookmarkedDevs, setBookmarkedDevs] = useState<BookmarkDeveloper[]>(loadBookmarked);

  useEffect(() => {
    saveBookmarked(bookmarkedDevs);
  }, [bookmarkedDevs]);

  const toggleBookmark = useCallback((dev: BookmarkDeveloper) => {
    setBookmarkedDevs((prev) => {
      const exists = prev.some((d) => d.id === dev.id);
      if (exists) {
        return prev.filter((d) => d.id !== dev.id);
      }
      return [...prev, dev];
    });
  }, []);

  return (
    <BookmarkContext.Provider value={{ bookmarkedDevs, toggleBookmark }}>
      {children}
    </BookmarkContext.Provider>
  );
}

export function useBookmarks(): BookmarkContextValue {
  const ctx = useContext(BookmarkContext);
  if (!ctx) {
    const devs: BookmarkDeveloper[] = builders.slice(0, 3).map((b) => ({
      id: b.id,
      name: b.name,
      role: b.role,
      avatar_url: b.avatar,
      location: b.country,
      experience: String(b.yearsExp),
      skills: b.skills,
    }));
    return {
      bookmarkedDevs: devs,
      toggleBookmark: () => {},
    };
  }
  return ctx;
}
