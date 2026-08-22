
/**
 * Local persistence for an in-progress project draft.
 *
 * This module was a set of no-op stubs:
 *
 * ```ts
 * export const saveDraftToLocalStorage = (data: ProjectDraftFormData) => {};
 * export const loadDraftFromLocalStorage = (): ProjectDraftFormData | null => null;
 * export const clearDraftFromLocalStorage = () => {};
 * ```
 *
 * so nothing was ever persisted and `restoreDraft()` always returned `null`.
 * The autosave hook was written against the intended contract, which is why
 * this went unnoticed: every call succeeded, silently doing nothing.
 *
 * Four things this is careful about:
 *
 * **`localStorage` can throw.** Safari in private browsing throws on
 * `setItem`, and every browser throws `QuotaExceededError` when full. An
 * autosave that takes the page down with it is worse than one that misses a
 * write, so every access is guarded and failures are returned rather than
 * raised.
 *
 * **It can be absent entirely.** This code runs during SSR, where there is no
 * `window`, and accessing `localStorage` throws outright when cookies are
 * blocked.
 *
 * **Stored data outlives the code that wrote it.** A draft saved by an older
 * build can have a shape the current form cannot render, so the payload
 * carries a schema version and anything else is discarded.
 *
 * **Drafts should not live forever.** One abandoned six months ago should not
 * resurface; entries past `DRAFT_MAX_AGE_MS` are treated as absent.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ProjectDraftFormData = any;

/** The `localStorage` key holding the draft envelope. */
export const DRAFT_STORAGE_KEY = "devlink.project-draft.v1";

/**
 * Bump when the shape of `ProjectDraftFormData` changes incompatibly. A stored
 * draft with a different version is discarded rather than handed to a form
 * that cannot render it.
 */
export const DRAFT_SCHEMA_VERSION = 1;

/** Drafts older than this are treated as absent. */
export const DRAFT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

interface DraftEnvelope {
  version: number;
  savedAt: number;
  data: ProjectDraftFormData;
}

/** What happened on a write, so the UI can say something useful. */
export type DraftStorageResult =
  | { ok: true }
  | { ok: false; reason: "unavailable" | "quota" | "error"; error?: unknown };

function getStorage(): Storage | null {
  try {
    if (typeof window === "undefined" || !window.localStorage) return null;
    return window.localStorage;
  } catch {
    // Reading the property itself throws when storage is blocked.
    return null;
  }
}

function isQuotaError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;

  // Chromium and Firefox use different names, and Firefox historically used
  // code 1014 with no useful name at all.
  return (
    error.name === "QuotaExceededError" ||
    error.name === "NS_ERROR_DOM_QUOTA_REACHED" ||
    (error as { code?: number }).code === 22 ||
    (error as { code?: number }).code === 1014
  );
}

/**
 * Persist a draft. Never throws.
 *
 * The result distinguishes "saved", "no storage here" and "storage is full",
 * because the last is the one worth telling the user about.
 */
export function saveDraftToLocalStorage(
  data: ProjectDraftFormData,
  now: number = Date.now(),
): DraftStorageResult {
  const storage = getStorage();
  if (!storage) return { ok: false, reason: "unavailable" };

  const envelope: DraftEnvelope = {
    version: DRAFT_SCHEMA_VERSION,
    savedAt: now,
    data,
  };

  try {
    storage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(envelope));
    return { ok: true };
  } catch (error) {
    if (isQuotaError(error)) return { ok: false, reason: "quota", error };
    return { ok: false, reason: "error", error };
  }
}

/**
 * Read the stored draft, or `null`.
 *
 * `null` covers every "nothing usable here" case — absent, unparseable,
 * written by an incompatible version, or too old. A caller only ever wants to
 * know whether there is a draft worth restoring.
 */
export function loadDraftFromLocalStorage(
  now: number = Date.now(),
): ProjectDraftFormData | null {
  const storage = getStorage();
  if (!storage) return null;

  let raw: string | null;
  try {
    raw = storage.getItem(DRAFT_STORAGE_KEY);
  } catch {
    return null;
  }

  if (!raw) return null;

  let envelope: unknown;
  try {
    envelope = JSON.parse(raw);
  } catch {
    // Corrupt entry. Clear it, or it fails on every subsequent load.
    clearDraftFromLocalStorage();
    return null;
  }

  if (
    typeof envelope !== "object" ||
    envelope === null ||
    (envelope as DraftEnvelope).version !== DRAFT_SCHEMA_VERSION
  ) {
    clearDraftFromLocalStorage();
    return null;
  }

  const { savedAt, data } = envelope as DraftEnvelope;

  if (typeof savedAt !== "number" || now - savedAt > DRAFT_MAX_AGE_MS) {
    clearDraftFromLocalStorage();
    return null;
  }

  return data ?? null;
}

/** Remove the stored draft. Never throws. */
export function clearDraftFromLocalStorage(): void {
  const storage = getStorage();
  if (!storage) return;

  try {
    storage.removeItem(DRAFT_STORAGE_KEY);
  } catch {
    // Nothing useful to do; it stays until the browser clears it.
  }
}

/** When the stored draft was written, or `null` if there is not one. */
export function getDraftSavedAt(): Date | null {
  const storage = getStorage();
  if (!storage) return null;

  try {
    const raw = storage.getItem(DRAFT_STORAGE_KEY);
    if (!raw) return null;

    const envelope = JSON.parse(raw) as DraftEnvelope;
    if (typeof envelope?.savedAt !== "number") return null;

    return new Date(envelope.savedAt);
  } catch {
    return null;
  }
}
