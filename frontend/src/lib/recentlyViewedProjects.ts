const STORAGE_KEY = "devlink-recently-viewed-projects";
const MAX_RECENT_PROJECTS = 5;

export function getRecentlyViewedProjectIds(): string[] {
  if (typeof window === "undefined") return [];

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

export function addRecentlyViewedProject(projectId: string): void {
  if (typeof window === "undefined") return;

  const current = getRecentlyViewedProjectIds();

  const updated = [projectId, ...current.filter((id) => id !== projectId)].slice(
    0,
    MAX_RECENT_PROJECTS,
  );

  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}
