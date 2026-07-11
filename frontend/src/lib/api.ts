import { toast } from "sonner";

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

  if (res.status === 204) {
    return undefined as unknown as TResponse;
  }

  const data: unknown = await res.json();
  return assertJson<TResponse>(data);
}

export async function applyToFlare(
  flareId: UUID,
  projectId: UUID,
  payload: {
    message?: string;
    portfolio_url?: string;
    github_url?: string;
  },
): Promise<ApplicationResponse> {
  const body: ApplicationCreatePayload = {
    project_id: projectId,
    flare_id: flareId,
    message: payload.message,
    portfolio_url: payload.portfolio_url,
    github_url: payload.github_url,
  };

  return requestJson<ApplicationResponse, ApplicationCreatePayload>({
    url: "/applications/",
    method: "POST",
    body,
  });
}

export async function getMyApplications(): Promise<ApplicationResponse[]> {
  return requestJson<ApplicationResponse[]>({
    url: "/applications/me",
    method: "GET",
  });
}

export async function getProjectApplications(projectId: UUID): Promise<ApplicationResponse[]> {
  return requestJson<ApplicationResponse[]>({
    url: `/applications/project/${projectId}`,
    method: "GET",
  });
}

export async function acceptApplication(id: UUID): Promise<ApplicationResponse> {
  return requestJson<ApplicationResponse>({
    url: `/applications/${id}/accept`,
    method: "PATCH",
  });
}

export async function rejectApplication(id: UUID): Promise<ApplicationResponse> {
  return requestJson<ApplicationResponse>({
    url: `/applications/${id}/reject`,
    method: "PATCH",
  });
}

export async function withdrawApplication(id: UUID): Promise<ApplicationResponse> {
  return requestJson<ApplicationResponse>({
    url: `/applications/${id}/withdraw`,
    method: "PATCH",
  });
}

export function toastError(err: unknown, fallback = "Something went wrong") {
  const message = err instanceof Error ? err.message : fallback;
  toast.error(message);
}
