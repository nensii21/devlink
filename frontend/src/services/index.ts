// Typed service facade. Delegates to the REST API layer (src/api) when
// VITE_API_BASE_URL is configured; otherwise falls back to local seed data
// so the UI stays fully functional in mock mode.
//
// The public shape of each service is unchanged, so no component needs edits.
// When your FastAPI backend is ready, set VITE_API_BASE_URL and all reads
// switch to the real endpoints automatically.

import * as seed from "@/mocks/seed";
import { hackathonStore } from "@/mocks/hackathonStore";
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
  recommendationsApi,
  fallbackTechStack,
  searchApi,
  issuesApi,
} from "@/api";
import type {
  BookmarkCollection,
  BookmarkCollectionWithBookmarks,
  Issue,
  IssueCreateInput,
  IssueUpdateInput,
  TechStackResponse,
} from "@/api";
import type { Hackathon, Flare, Message } from "@/mocks/seed";

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
  list: (params?: Record<string, unknown>) =>
    withFallback(() => projectsApi.list(params), seed.projects),
  get: (id: string) =>
    withFallback(() => projectsApi.get(id), seed.projects.find((p) => p.id === id) ?? null),
  trending: () =>
    withFallback(
      () => projectsApi.trending(),
      [...seed.projects].sort((a, b) => b.stars - a.stars).slice(0, 5),
    ),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  createDraft: (body: any) => withFallback(() => projectsApi.createDraft(body as any), {} as any),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  updateDraft: (id: string, body: any) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    withFallback(() => projectsApi.updateDraft(id, body as any), {} as any),
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
  quickActions: () =>
    withFallback<typeof seed.quickActions>(
      async () =>
        ((await analyticsApi.dashboard()).quickActions as unknown as typeof seed.quickActions) ??
        seed.quickActions,
      seed.quickActions,
    ),
};

export const activitiesService = {
  list: (limit = 20) => fetchJson<BackendActivity[]>(`/activities/?limit=${limit}`),
  user: (userId: string) =>
    withFallback(() => fetchJson<BackendActivity[]>(`/activities/user/${userId}`), [
      {
        id: `act-${Date.now()}-1`,
        actor_id: userId,
        activity_type: "project_created",
        title: "Created a Project",
        description: "Started a new project repository.",
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: `act-${Date.now()}-2`,
        actor_id: userId,
        activity_type: "profile_updated",
        title: "Updated Profile",
        description: "Added new skills and experience.",
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: `act-${Date.now()}-3`,
        actor_id: userId,
        activity_type: "user_registered",
        title: "Joined DevLink",
        description: "Welcome to the community!",
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ] as BackendActivity[]),
};

export const flaresService = {
  list: () =>
    withFallback(
      () => postsApi.list(),
      seed.flares.filter((f) => !f.status || f.status === "published"),
    ),
  drafts: () =>
    withFallback(
      () => postsApi.drafts(),
      seed.flares.filter((f) => f.status === "draft" || f.status === "scheduled"),
    ),
  create: (body: { content: string; tags?: string[]; status?: string; publish_at?: string }) =>
    withFallback(() => postsApi.create(body), {
      id: `mock-${Date.now()}`,
      author: {
        ...seed.builders[0],
        name: seed.currentUser.name,
        handle: seed.currentUser.handle,
        avatar: seed.currentUser.avatar,
      },
      content: body.content,
      tags: body.tags ?? [],
      likes: 0,
      comments: 0,
      ago: "just now",
      status: body.status ?? "published",
      publish_at: body.publish_at,
    } as unknown as Flare),
  update: (id: string, body: Partial<Flare & { status?: string; publish_at?: string }>) =>
    withFallback(() => postsApi.update(id, body), {
      id,
      ...body,
    } as unknown as Flare),
  remove: (id: string) =>
    withFallback<void>(async () => {
      await postsApi.remove(id);
    }, undefined),
};

export const messagesService = {
  conversations: () => withFallback(() => messagesApi.conversations(), seed.conversations),
  thread: async (id: string) => {
    let currentUser: { id?: string } | null = null;
    if (isBackendConfigured()) {
      try {
        const u = (await authApi.me()) as unknown as { id?: string };
        currentUser = { id: u.id };
      } catch {
        // Ignored
      }
    }
    return withFallback(async () => {
      const msgs = await messagesApi.thread(id);
      return msgs.map(
        (m: {
          id: string;
          sender_id?: string;
          content?: string;
          created_at?: string;
          type?: string;
          attachment_url?: string;
          attachment_name?: string;
          attachment_size?: number;
          mime_type?: string;
          reactions?: {
            id: string;
            user_id: string;
            emoji: string;
            created_at: string;
          }[];
        }): seed.Message => ({
          id: m.id,
          from: m.sender_id === currentUser?.id ? "me" : (m.sender_id ?? "me"),
          text: m.content ?? "",
          at: m.created_at
            ? new Date(m.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : "",
          type: m.type ?? "text",
          attachment_url: m.attachment_url,
          attachment_name: m.attachment_name,
          attachment_size: m.attachment_size,
          reactions: m.reactions || [],
        }));
      },
      seed.messages[id] ?? [],
    );
  },
  send: (
    conversationId: string,
    text: string,
    attachment?: {
      url: string;
      name: string;
      size: number;
      mime_type: string;
      type: string;
    },
  ) =>
    withFallback(
      () =>
        messagesApi.send({
          conversation_id: conversationId,
          content: text,
          type: attachment?.type || "text",
          attachment_url: attachment?.url,
          attachment_name: attachment?.name,
          attachment_size: attachment?.size,
          mime_type: attachment?.mime_type,
        }),
      {
        id: `msg-${Date.now()}`,
        from: "me",
        text,
        at: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        type: attachment?.type || "text",
        attachment_url: attachment?.url,
        attachment_name: attachment?.name,
        attachment_size: attachment?.size,
        mime_type: attachment?.mime_type,
      },
    ),
  addReaction: (messageId: string, emoji: string) =>
    withFallback(() => messagesApi.addReaction(messageId, emoji), {
      id: `reaction-${Date.now()}`,
      user_id: "me",
      emoji,
      created_at: new Date().toISOString(),
    }),
  removeReaction: (messageId: string, emoji: string) =>
    withFallback(() => messagesApi.removeReaction(messageId, emoji), undefined),
};

export const issuesService = {
  list: (projectId: string, params?: { status?: string; skip?: number; limit?: number }) =>
    isBackendConfigured() ? issuesApi.list(projectId, params) : Promise.resolve([]),

  get: (projectId: string, issueId: string) =>
    isBackendConfigured()
      ? issuesApi.get(projectId, issueId)
      : Promise.reject("Not implemented in mock"),

  create: (projectId: string, body: IssueCreateInput) =>
    isBackendConfigured()
      ? issuesApi.create(projectId, body)
      : Promise.reject("Not implemented in mock"),

  update: (projectId: string, issueId: string, body: IssueUpdateInput) =>
    isBackendConfigured()
      ? issuesApi.update(projectId, issueId, body)
      : Promise.reject("Not implemented in mock"),

  remove: (projectId: string, issueId: string) =>
    isBackendConfigured()
      ? issuesApi.remove(projectId, issueId)
      : Promise.reject("Not implemented in mock"),

  checkDuplicates: (
    projectId: string,
    body: { title: string; description: string; threshold?: number },
  ) =>
    isBackendConfigured()
      ? issuesApi.checkDuplicates(projectId, body)
      : Promise.reject("Not implemented in mock"),

  markAsDuplicate: (projectId: string, issueId: string, duplicateOfId: string) =>
    isBackendConfigured()
      ? issuesApi.markAsDuplicate(projectId, issueId, duplicateOfId)
      : Promise.reject("Not implemented in mock"),

  estimateDifficulty: (projectId: string, issueId: string) =>
    isBackendConfigured()
      ? issuesApi.estimateDifficulty(projectId, issueId)
      : Promise.reject("Not implemented in mock"),

  overrideDifficulty: (projectId: string, issueId: string, difficulty: Issue["difficulty"]) =>
    isBackendConfigured()
      ? issuesApi.overrideDifficulty(projectId, issueId, difficulty)
      : Promise.reject("Not implemented in mock"),
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
  list: () =>
    isBackendConfigured()
      ? hackathonsApi.list().catch(() => hackathonStore.getAll())
      : mock(hackathonStore.getAll()),

  get: (id: string) =>
    isBackendConfigured()
      ? hackathonsApi.get(id).catch(() => hackathonStore.getById(id))
      : mock(hackathonStore.getById(id)),

  create: (body: Partial<Hackathon>) =>
    isBackendConfigured()
      ? hackathonsApi.create(body).catch(() => hackathonStore.create(body))
      : hackathonStore.create(body),

  update: (id: string, body: Partial<Hackathon>) =>
    withFallback(() => hackathonsApi.update(id, body), null),

  delete: (id: string) => withFallback(() => hackathonsApi.delete(id), undefined),

  register: (id: string, body?: { motivation?: string }) =>
    isBackendConfigured() ? hackathonsApi.register(id, body) : hackathonStore.register(id),

  cancelRegistration: (id: string) =>
    isBackendConfigured()
      ? hackathonsApi.cancelRegistration(id)
      : hackathonStore.cancelRegistration(id),

  isRegistered: (id: string) => !isBackendConfigured() && hackathonStore.isRegistered(id),

  getTeams: (id: string) =>
    isBackendConfigured()
      ? hackathonsApi.getTeams(id).catch(() => hackathonStore.getTeams(id))
      : mock(hackathonStore.getTeams(id)),

  createTeam: (id: string, body: { name: string; description?: string }) =>
    isBackendConfigured()
      ? hackathonsApi.createTeam(id, body)
      : hackathonStore.createTeam(id, body),

  joinTeam: (teamId: string) =>
    isBackendConfigured() ? hackathonsApi.joinTeam(teamId) : hackathonStore.joinTeam(teamId),

  leaveTeam: (teamId: string) =>
    isBackendConfigured() ? hackathonsApi.leaveTeam(teamId) : hackathonStore.leaveTeam(teamId),

  getSubmissions: (id: string) =>
    isBackendConfigured()
      ? hackathonsApi.getSubmissions(id).catch(() => hackathonStore.getSubmissions(id))
      : mock(hackathonStore.getSubmissions(id)),

  createSubmission: (
    id: string,
    body: {
      team_id: string;
      title: string;
      description: string;
      repo_url?: string;
      demo_url?: string;
    },
  ) =>
    isBackendConfigured()
      ? hackathonsApi.createSubmission(id, body)
      : hackathonStore.createSubmission(id, body),

  getLeaderboard: (id: string) =>
    isBackendConfigured()
      ? hackathonsApi.getLeaderboard(id).catch(() => hackathonStore.getLeaderboard(id))
      : mock(hackathonStore.getLeaderboard(id)),
};

export const techStackService = {
  recommend: (projectIdea: string) =>
    withFallback(
      () => recommendationsApi.recommendTechStack(projectIdea),
      fallbackTechStack(projectIdea),
    ),
};

export const searchService = {
  autocomplete: (q: string) =>
    withFallback(
      async () => {
        const res = await searchApi.autocomplete(q);
        return res;
      },
      {
        users: [],
        projects: [],
        skills: [],
        organizations: [],
        tags: [],
      },
    ), // In fallback we could just return empty or mock data, but we'll handle mock logic in the component for offline mode, or we can add it here.
};

export const userService = {
  me: () =>
    withFallback(async () => {
      const u = await authApi.me();
      return {
        id: u.id,
        name: u.full_name ?? u.username,
        handle: u.username,
        avatar: u.profile_image ?? u.avatar ?? seed.currentUser.avatar,
        premium: (u as unknown as { premium?: boolean }).premium ?? false,
        verified: (u as unknown as { is_verified?: boolean }).is_verified ?? false,
      };
    }, seed.currentUser),
};

export { teamMatchService } from "./teamMatch";
export { auditService } from "./audit";

export type {
  Builder,
  Project,
  Activity,
  Flare,
  Conversation,
  Notification,
  Hackathon,
  HackathonTeam,
  HackathonSubmission,
  HackathonLeaderboardEntry,
  Deadline,
  QuickAction,
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
