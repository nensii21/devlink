// Typed service facade. Delegates to the REST API layer (src/api) when
// VITE_API_BASE_URL is configured; otherwise falls back to local seed data
// so the UI stays fully functional in mock mode.
//
// The public shape of each service is unchanged, so no component needs edits.
// When your FastAPI backend is ready, set VITE_API_BASE_URL and all reads
// switch to the real endpoints automatically.

import * as seed from "@/mocks/seed";
import {
  isBackendConfigured,
  projectsApi,
  buildersApi,
  postsApi,
  messagesApi,
  notificationsApi,
  hackathonsApi,
  analyticsApi,
  authApi,
  collectionsApi,
} from "@/api";
import type { BookmarkCollection, BookmarkCollectionWithBookmarks } from "@/api";

const delay = 120;
const mock = <T>(v: T): Promise<T> => new Promise((r) => setTimeout(() => r(v), delay));

// Wrap a real API call so a network/backend failure silently degrades to the
// provided fallback. Keeps every page usable if the backend is unreachable.
async function withFallback<T>(call: () => Promise<T>, fallback: T): Promise<T> {
  if (!isBackendConfigured()) return mock(fallback);
  try {
    return await call();
  } catch (err) {
    if (import.meta.env.DEV) console.warn("[services] API call failed, using fallback:", err);
    return fallback;
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export interface ActivityActor {
  id: string;
  first_name: string;
  last_name: string;
  username: string;
  profile_image?: string | null;
}

export interface BackendActivity {
  id: string;
  actor_id: string;
  actor?: ActivityActor | null;
  activity_type: string;
  title: string;
  description?: string | null;
  project_id?: string | null;
  organization_id?: string | null;
  repository_id?: string | null;
  application_id?: string | null;
  builder_flare_id?: string | null;
  icon?: string | null;
  color?: string | null;
  created_at: string;
}

export const projectsService = {
  list: () => withFallback(() => projectsApi.list(), seed.projects),
  get: (id: string) =>
    withFallback(() => projectsApi.get(id), seed.projects.find((p) => p.id === id) ?? null),
  trending: () =>
    withFallback(
      () => projectsApi.trending(),
      [...seed.projects].sort((a, b) => b.stars - a.stars).slice(0, 5),
    ),
};

export const buildersService = {
  list: () => withFallback(() => buildersApi.list(), seed.builders),
  get: (id: string) =>
    withFallback(() => buildersApi.get(id), seed.builders.find((b) => b.id === id) ?? null),
  suggested: () => withFallback(() => buildersApi.trending(), seed.builders.slice(3, 6)),
  matches: () =>
    withFallback(
      () => buildersApi.matches(),
      [...seed.builders].sort((a, b) => b.matchScore - a.matchScore),
    ),
};

export const dashboardService = {
  stats: () =>
    withFallback<typeof seed.stats>(
      async () =>
        ((await analyticsApi.dashboard()).stats as unknown as typeof seed.stats) ?? seed.stats,
      seed.stats,
    ),
  activity: () =>
    withFallback<typeof seed.activity>(
      async () =>
        ((await analyticsApi.dashboard()).activity as unknown as typeof seed.activity) ??
        seed.activity,
      seed.activity,
    ),
  builderRequests: () =>
    withFallback<typeof seed.builderRequests>(
      async () =>
        ((await analyticsApi.dashboard())
          .builder_requests as unknown as typeof seed.builderRequests) ?? seed.builderRequests,
      seed.builderRequests,
    ),
  inviteRequests: () =>
    withFallback<typeof seed.inviteRequests>(
      async () =>
        ((await analyticsApi.dashboard())
          .invite_requests as unknown as typeof seed.inviteRequests) ?? seed.inviteRequests,
      seed.inviteRequests,
    ),
  deadlines: () =>
    withFallback<typeof seed.deadlines>(
      async () =>
        ((await analyticsApi.dashboard()).deadlines as unknown as typeof seed.deadlines) ??
        seed.deadlines,
      seed.deadlines,
    ),
};

export const activitiesService = {
  list: (limit = 20) => fetchJson<BackendActivity[]>(`/activities/?limit=${limit}`),
  user: (userId: string) => fetchJson<BackendActivity[]>(`/activities/user/${userId}`),
};

export const flaresService = {
  list: () => withFallback(() => postsApi.list(), seed.flares),
};

export const messagesService = {
  conversations: () => withFallback(() => messagesApi.conversations(), seed.conversations),
  thread: (id: string) => withFallback(() => messagesApi.thread(id), seed.messages[id] ?? []),
};

export const notificationsService = {
  list: async () => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("devlink-notifications");
        if (stored) {
          const local = JSON.parse(stored);
          return [...local, ...seed.notifications];
        }
      } catch (error) {
        console.debug("Failed to load notifications:", error);
      }
    }

    return withFallback(() => notificationsApi.list(), seed.notifications);
  },
};

export const hackathonsService = {
  list: () => withFallback(() => hackathonsApi.list(), seed.hackathons),
};

export const userService = {
  me: () =>
    withFallback(async () => {
      const u = await authApi.me();
      return {
        id: u.id,
        name: u.full_name ?? u.username,
        handle: u.username,
        avatar: u.avatar ?? seed.currentUser.avatar,
        premium: (u as unknown as { premium?: boolean }).premium ?? false,
      };
    }, seed.currentUser),
};

export type {
  Builder,
  Project,
  Activity,
  Flare,
  Conversation,
  Notification,
  Hackathon,
  Deadline,
} from "@/mocks/seed";

const COLLECTIONS_STORAGE_KEY = "devlink-collections";
const COLLECTIONS_BOOKMARKS_KEY = "devlink-collection-bookmarks";

function loadLocalCollections(): BookmarkCollection[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(COLLECTIONS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveLocalCollections(collections: BookmarkCollection[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(COLLECTIONS_STORAGE_KEY, JSON.stringify(collections));
}

function loadLocalCollectionBookmarks(): Record<string, string[]> {
  if (typeof window === "undefined") return {};
  try {
    const stored = localStorage.getItem(COLLECTIONS_BOOKMARKS_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

function saveLocalCollectionBookmarks(data: Record<string, string[]>): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(COLLECTIONS_BOOKMARKS_KEY, JSON.stringify(data));
}

function ensureLocalDefaultCollection(): BookmarkCollection {
  const collections = loadLocalCollections();
  const existing = collections.find((c) => c.is_default);
  if (existing) return existing;

  const defaultCol: BookmarkCollection = {
    id: "col-default",
    user_id: "me",
    name: "All Bookmarks",
    is_default: true,
    bookmark_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  collections.unshift(defaultCol);
  saveLocalCollections(collections);
  return defaultCol;
}

function generateLocalId(): string {
  return `col-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const collectionsService = {
  list: async (): Promise<BookmarkCollection[]> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.list();
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    ensureLocalDefaultCollection();
    const collections = loadLocalCollections();
    const bookmarksByCol = loadLocalCollectionBookmarks();

    return collections.map((col) => ({
      ...col,
      bookmark_count: (bookmarksByCol[col.id] ?? []).length,
    }));
  },

  get: async (id: string): Promise<BookmarkCollectionWithBookmarks> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.get(id);
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const collections = loadLocalCollections();
    const col = collections.find((c) => c.id === id);
    if (!col) {
      throw new Error("Collection not found");
    }

    const bookmarksByCol = loadLocalCollectionBookmarks();
    const bookmarkIds = bookmarksByCol[id] ?? [];

    return {
      ...col,
      bookmark_count: bookmarkIds.length,
      bookmarks: bookmarkIds.map((bookmarkId, idx) => ({
        id: `bm-${bookmarkId}`,
        user_id: "me",
        project_id: bookmarkId,
        created_at: new Date(Date.now() - idx * 1000).toISOString(),
      })),
    };
  },

  create: async (name: string): Promise<BookmarkCollection> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.create(name);
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const collections = loadLocalCollections();
    const duplicate = collections.find((c) => c.name.toLowerCase() === name.toLowerCase());
    if (duplicate) {
      throw new Error("A collection with this name already exists");
    }

    const newCol: BookmarkCollection = {
      id: generateLocalId(),
      user_id: "me",
      name,
      is_default: false,
      bookmark_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    collections.push(newCol);
    saveLocalCollections(collections);
    return newCol;
  },

  rename: async (id: string, name: string): Promise<BookmarkCollection> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.rename(id, name);
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const collections = loadLocalCollections();
    const col = collections.find((c) => c.id === id);
    if (!col) throw new Error("Collection not found");
    if (col.is_default) throw new Error("Cannot rename the default collection");

    const duplicate = collections.find(
      (c) => c.id !== id && c.name.toLowerCase() === name.toLowerCase(),
    );
    if (duplicate) {
      throw new Error("A collection with this name already exists");
    }

    col.name = name;
    col.updated_at = new Date().toISOString();
    saveLocalCollections(collections);

    const bookmarksByCol = loadLocalCollectionBookmarks();
    return {
      ...col,
      bookmark_count: (bookmarksByCol[col.id] ?? []).length,
    };
  },

  delete: async (id: string): Promise<void> => {
    if (isBackendConfigured()) {
      try {
        await collectionsApi.delete(id);
        return;
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const collections = loadLocalCollections();
    const col = collections.find((c) => c.id === id);
    if (!col) throw new Error("Collection not found");
    if (col.is_default) throw new Error("Cannot delete the default collection");

    const updated = collections.filter((c) => c.id !== id);
    saveLocalCollections(updated);

    const bookmarksByCol = loadLocalCollectionBookmarks();
    delete bookmarksByCol[id];
    saveLocalCollectionBookmarks(bookmarksByCol);
  },

  addBookmark: async (
    collectionId: string,
    bookmarkId: string,
  ): Promise<{ success: boolean; bookmark_count: number }> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.addBookmark(collectionId, bookmarkId);
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const bookmarksByCol = loadLocalCollectionBookmarks();
    if (!bookmarksByCol[collectionId]) {
      bookmarksByCol[collectionId] = [];
    }

    if (!bookmarksByCol[collectionId].includes(bookmarkId)) {
      bookmarksByCol[collectionId].push(bookmarkId);
    }

    saveLocalCollectionBookmarks(bookmarksByCol);

    const collections = loadLocalCollections();
    const col = collections.find((c) => c.id === collectionId);
    if (col) {
      col.bookmark_count = bookmarksByCol[collectionId].length;
      saveLocalCollections(collections);
    }

    return {
      success: true,
      bookmark_count: bookmarksByCol[collectionId].length,
    };
  },

  removeBookmark: async (collectionId: string, bookmarkId: string): Promise<void> => {
    if (isBackendConfigured()) {
      try {
        await collectionsApi.removeBookmark(collectionId, bookmarkId);
        return;
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const bookmarksByCol = loadLocalCollectionBookmarks();
    if (bookmarksByCol[collectionId]) {
      bookmarksByCol[collectionId] = bookmarksByCol[collectionId].filter((id) => id !== bookmarkId);
      saveLocalCollectionBookmarks(bookmarksByCol);
    }

    const collections = loadLocalCollections();
    const col = collections.find((c) => c.id === collectionId);
    if (col) {
      col.bookmark_count = (bookmarksByCol[collectionId] ?? []).length;
      saveLocalCollections(collections);
    }
  },

  getBookmarkCollections: async (bookmarkId: string): Promise<BookmarkCollection[]> => {
    if (isBackendConfigured()) {
      try {
        return await collectionsApi.getBookmarkCollections(bookmarkId);
      } catch (err) {
        if (import.meta.env.DEV)
          console.warn("[services] collections API failed, using fallback:", err);
      }
    }

    const collections = loadLocalCollections();
    const bookmarksByCol = loadLocalCollectionBookmarks();

    return collections.filter((col) => bookmarksByCol[col.id]?.includes(bookmarkId));
  },
};
