"use client";
import { toast } from "sonner";
import { api } from "../api/client";

export default api;

export type ProjectSearchResult = {
  id: string;
  title: string;
  slug: string;
};
type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export type ApplicationStatus = "pending" | "reviewing" | "accepted" | "rejected" | "withdrawn";

export type UUID = string;

export type ApplicationResponse = {
  id: UUID;
  applicant_id: UUID;
  project_id: UUID;
  flare_id: UUID;
  status: ApplicationStatus;
  message: string | null;
  portfolio_url: string | null;
  github_url: string | null;
  resume_url: string | null;
  review_notes: string | null;
  shortlisted: boolean;
  created_at: string;
  updated_at: string;
};

export type ApplicationCreatePayload = {
  project_id: UUID;
  flare_id: UUID;
  message?: string;
  portfolio_url?: string;
  github_url?: string;
  resume_url?: string;
};

export type ApplicationUpdatePayload = {
  message?: string | null;
  portfolio_url?: string | null;
  github_url?: string | null;
  resume_url?: string | null;
  review_notes?: string | null;
  shortlisted?: boolean;
  status?: ApplicationStatus;
};

export type DeveloperSearchResult = {
  id: string;
  username: string;
  headline: string;
};

async function fetchJson<T>(signal: AbortSignal, url: string): Promise<T> {
  const response = await fetch(url, { method: "GET", signal });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

type ApiConfig = {
  baseUrl: string;
};

function getApiConfig(): ApiConfig {
  const baseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

  return {
    baseUrl: baseUrl && baseUrl.trim().length > 0 ? baseUrl : "",
  };
}

function assertJson<T>(data: unknown): T {
  return data as T;
}

async function requestJson<TResponse, TBody extends JsonValue | undefined = undefined>(input: {
  url: string;
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: TBody;
}): Promise<TResponse> {
  const { baseUrl } = getApiConfig();

  const res = await fetch(`${baseUrl}${input.url}`, {
    method: input.method,
    headers: input.body === undefined ? undefined : { "content-type": "application/json" },
    body: input.body === undefined ? undefined : JSON.stringify(input.body),
    credentials: "include",
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;

    try {
      const data: unknown = await res.json();
      if (typeof data === "object" && data !== null) {
        const maybe = data as Record<string, JsonValue>;
        const m = maybe["detail"] ?? maybe["message"];
        if (typeof m === "string") message = m;
      }
    } catch {
      // ignore json parse errors
    }

    throw new Error(message);
  }
  return (await res.json()) as TResponse;
}

export async function searchProjects(
  query: string,
  signal: AbortSignal,
): Promise<ProjectSearchResult[]> {
  const params = new URLSearchParams({ query });
  return fetchJson<ProjectSearchResult[]>(signal, `/api/projects?${params.toString()}`);
}

export async function searchUsers(
  query: string,
  signal: AbortSignal,
): Promise<DeveloperSearchResult[]> {
  const params = new URLSearchParams({ query });
  return fetchJson<DeveloperSearchResult[]>(signal, `/api/users?${params.toString()}`);
}

export async function rejectApplication(id: UUID): Promise<ApplicationResponse> {
  return api.patch<ApplicationResponse>(`/applications/${id}/reject`);
}

export async function withdrawApplication(id: UUID): Promise<ApplicationResponse> {
  return api.patch<ApplicationResponse>(`/applications/${id}/withdraw`);
}

export function toastError(err: unknown, fallback = "Something went wrong") {
  const message = err instanceof Error ? err.message : fallback;
  toast.error(message);
}

export type FollowStatusResponse = {
  is_following: boolean;
  follower_count: number;
  following_count: number;
};

export type FollowerItem = {
  id: string;
  follower_id: string;
  following_id: string;
  created_at: string;
};

export type PaginatedFollowersResult = {
  items: FollowerItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
};

export async function getFollowStatus(userId: UUID): Promise<FollowStatusResponse> {
  return api.get<FollowStatusResponse>(`/api/followers/${userId}/status`);
}

export async function getFollowers(
  userId: UUID,
  params?: { page?: number; limit?: number },
): Promise<PaginatedFollowersResult> {
  return api.get<PaginatedFollowersResult>(`/followers/${userId}`, {
    query: {
      page: params?.page ?? 1,
      limit: params?.limit ?? 20,
    },
  });
}

export async function getFollowing(
  userId: UUID,
  params?: { page?: number; limit?: number },
): Promise<PaginatedFollowersResult> {
  return api.get<PaginatedFollowersResult>(`/followers/${userId}/following`, {
    query: {
      page: params?.page ?? 1,
      limit: params?.limit ?? 20,
    },
  });
}

export async function followUser(userId: UUID): Promise<FollowStatusResponse> {
  await api.post<void>(`/api/followers/${userId}`);
  return getFollowStatus(userId);
}

export async function unfollowUser(userId: UUID): Promise<FollowStatusResponse> {
  await api.delete<void>(`/api/followers/${userId}`);
  return getFollowStatus(userId);
}

export type FollowerResponse = {
  id: UUID;
  follower_id: UUID;
  following_id: UUID;
  created_at: string;
  follower?: {
    id: UUID;
    first_name: string;
    last_name: string;
    username: string;
    headline?: string;
    profile_image?: string;
  };
  following?: {
    id: UUID;
    first_name: string;
    last_name: string;
    username: string;
    headline?: string;
    profile_image?: string;
  };
};



export async function getMyApplications(): Promise<ApplicationResponse[]> {
  return api.get<ApplicationResponse[]>("/applications/my");
}

export async function acceptApplication(id: UUID): Promise<ApplicationResponse> {
  return api.patch<ApplicationResponse>(`/applications/${id}/accept`);
}

export async function getProjectApplications(projectId: UUID): Promise<ApplicationResponse[]> {
  return api.get<ApplicationResponse[]>(`/projects/${projectId}/applications`);
}

export async function applyToFlare(
  flareId: UUID,
  projectId: UUID,
  payload: Omit<ApplicationCreatePayload, "project_id" | "flare_id">,
): Promise<ApplicationResponse> {
  return api.post<ApplicationResponse>("/applications", {
    ...payload,
    project_id: projectId,
    flare_id: flareId,
  });
}

export async function getProjectBuilderFlares(
  projectId: UUID,
): Promise<{ id: UUID; role: string; title: string; openings: number; status: string }[]> {
  return api.get(`/builder-flares/project/${projectId}`);
}
