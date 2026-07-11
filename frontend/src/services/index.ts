// Typed mock services. Swap `mock()` for real fetch calls later.
import * as seed from "@/mocks/seed";

const mock = <T>(v: T, delay = 120): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), delay));

export const projectsService = {
  list: () => mock(seed.projects),
  get: (id: string) => mock(seed.projects.find((p) => p.id === id) ?? null),
  trending: () => mock([...seed.projects].sort((a, b) => b.stars - a.stars).slice(0, 5)),
};

export const buildersService = {
  list: () => mock(seed.builders),
  get: (id: string) => mock(seed.builders.find((b) => b.id === id) ?? null),
  suggested: () => mock(seed.builders.slice(3, 6)),
  matches: () => mock([...seed.builders].sort((a, b) => b.matchScore - a.matchScore)),
};

export const dashboardService = {
  stats: () => mock(seed.stats),
  activity: () => mock(seed.activity),
  builderRequests: () => mock(seed.builderRequests),
  inviteRequests: () => mock(seed.inviteRequests),
  deadlines: () => mock(seed.deadlines),
};

export const flaresService = {
  list: () => mock(seed.flares),
};

export const messagesService = {
  conversations: () => mock(seed.conversations),
  thread: (id: string) => mock(seed.messages[id] ?? []),
};

export const notificationsService = {
  list: () => mock(seed.notifications),
};

export const hackathonsService = {
  list: () => mock(seed.hackathons),
};

export const userService = {
  me: () => mock(seed.currentUser),
};

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface SearchResult {
  users: any[];
  projects: any[];
  skills: any[];
  flares: any[];
}

export const searchService = {
  globalSearch: async (query: string): Promise<SearchResult> => {
    if (!query || query.trim() === "") {
      return { users: [], projects: [], skills: [], flares: [] };
    }
    const response = await fetch(`${API_URL}/search/?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error("Search request failed");
    }
    return response.json();
  },
};

export type { Builder, Project, Activity, Flare, Conversation, Notification, Hackathon, Deadline } from "@/mocks/seed";

