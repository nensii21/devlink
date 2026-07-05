const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export interface ProfilePayload {
  headline?: string | null;
  bio?: string | null;
  location?: string | null;
  timezone?: string | null;
  website?: string | null;
  portfolio_url?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  role?: string | null;
  experience_level?: string | null;
  company?: string | null;
}

export interface ProfileSkillPayload {
  name: string;
  level?: string;
  category?: string;
  years_of_experience?: number;
}

export async function getCurrentUserProfile() {
  return request<unknown>("/users/me");
}

export async function updateCurrentUserProfile(payload: ProfilePayload) {
  return request<unknown>("/users/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function listSkills() {
  return request<unknown[]>("/skills");
}

export async function createUserSkill(payload: ProfileSkillPayload) {
  return request<unknown>("/user_skills", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateUserSkill(skillId: string, payload: ProfileSkillPayload) {
  return request<unknown>(`/user_skills/${skillId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteUserSkill(skillId: string) {
  return request<unknown>(`/user_skills/${skillId}`, {
    method: "DELETE",
  });
}
