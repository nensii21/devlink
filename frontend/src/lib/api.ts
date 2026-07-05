"use client";

export type ProjectSearchResult = {
  id: string;
  title: string;
  slug: string;
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
  return (await response.json()) as T;
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
