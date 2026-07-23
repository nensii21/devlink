import { useEffect, useRef, useCallback, useState } from "react";
import {
  saveDraftToLocalStorage,
  loadDraftFromLocalStorage,
  clearDraftFromLocalStorage,
  type ProjectDraftFormData,
} from "@/lib/projectDraft";
import { projectsService } from "@/services";

const AUTO_SAVE_DELAY_MS = 30000;
const LOCAL_STORAGE_DEBOUNCE_MS = 1000;

export function useProjectDraftAutoSave(formData: ProjectDraftFormData) {
  const [backendProjectId, setBackendProjectId] = useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autoSaveTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const formDataRef = useRef(formData);

  formDataRef.current = formData;

  const saveToBackend = useCallback(
    async (data: ProjectDraftFormData) => {
      if (!data.title.trim()) return;

      setIsSaving(true);
      try {
        if (backendProjectId) {
          const result = await projectsService.updateDraft(backendProjectId, {
            title: data.title,
            slug: data.slug,
            description: data.description || undefined,
            tagline: data.tagline || undefined,
            stage: data.stage || undefined,
            visibility: data.visibility || undefined,
            tech_stack: data.tech_stack || undefined,
            repository_url: data.repository_url || undefined,
            website_url: data.website_url || undefined,
            demo_url: data.demo_url || undefined,
            team_size: data.team_size,
            max_team_size: data.max_team_size,
            hiring: data.hiring,
            logo_url: data.logo_url || undefined,
            banner_url: data.banner_url || undefined,
          });
          if (result) {
            setLastSavedAt(new Date());
          }
        } else {
          const result = await projectsService.createDraft({
            title: data.title,
            slug: data.slug,
            description: data.description || undefined,
            tagline: data.tagline || undefined,
            stage: data.stage || undefined,
            visibility: data.visibility || undefined,
            tech_stack: data.tech_stack || undefined,
            repository_url: data.repository_url || undefined,
            website_url: data.website_url || undefined,
            demo_url: data.demo_url || undefined,
            team_size: data.team_size,
            max_team_size: data.max_team_size,
            hiring: data.hiring,
            logo_url: data.logo_url || undefined,
            banner_url: data.banner_url || undefined,
          });
          if (result && "id" in result) {
            setBackendProjectId(result.id as string);
            setLastSavedAt(new Date());
          }
        }
      } catch (error) {
        console.debug("Failed to save draft to backend:", error);
      } finally {
        setIsSaving(false);
      }
    },
    [backendProjectId],
  );

  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      saveDraftToLocalStorage(formData);
    }, LOCAL_STORAGE_DEBOUNCE_MS);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [formData]);

  useEffect(() => {
    autoSaveTimerRef.current = setInterval(() => {
      if (formDataRef.current.title.trim()) {
        saveToBackend(formDataRef.current);
      }
    }, AUTO_SAVE_DELAY_MS);

    return () => {
      if (autoSaveTimerRef.current) {
        clearInterval(autoSaveTimerRef.current);
      }
    };
  }, [saveToBackend]);

  const restoreDraft = useCallback((): ProjectDraftFormData | null => {
    return loadDraftFromLocalStorage();
  }, []);

  const clearDraft = useCallback(() => {
    clearDraftFromLocalStorage();
    setBackendProjectId(null);
    setLastSavedAt(null);
  }, []);

  const saveNow = useCallback(async () => {
    if (formDataRef.current.title.trim()) {
      saveDraftToLocalStorage(formDataRef.current);
      await saveToBackend(formDataRef.current);
    }
  }, [saveToBackend]);

  return {
    backendProjectId,
    lastSavedAt,
    isSaving,
    restoreDraft,
    clearDraft,
    saveNow,
  };
}
