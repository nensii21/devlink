// Typed mock services. Swap `mock()` for real fetch calls later.
import * as seed from "@/mocks/seed";

const mock = <T>(v: T, delay = 120): Promise<T> =>
  new Promise((r) => setTimeout(() => r(v), delay));

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

export const activitiesService = {
  list: (limit = 20) => fetchJson<BackendActivity[]>(`/activities/?limit=${limit}`),
  user: (userId: string) => fetchJson<BackendActivity[]>(`/activities/user/${userId}`),
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
