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

export type { Builder, Project, Activity, Flare, Conversation, Notification, Hackathon, Deadline } from "@/mocks/seed";
