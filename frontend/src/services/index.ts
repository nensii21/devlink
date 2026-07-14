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
} from "@/api";

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
