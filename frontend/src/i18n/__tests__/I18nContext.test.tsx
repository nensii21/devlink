import { act, render, renderHook, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { I18nProvider, useTranslation } from "@/context/I18nContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

const STORAGE_KEY = "devlink-locale";

function wrapper({ children }: { children: ReactNode }) {
  return <I18nProvider>{children}</I18nProvider>;
}

function setLanguages(languages: string[]) {
  Object.defineProperty(window.navigator, "languages", {
    configurable: true,
    value: languages,
  });
  Object.defineProperty(window.navigator, "language", {
    configurable: true,
    value: languages[0],
  });
}

beforeEach(() => {
  localStorage.clear();
  setLanguages(["en-US"]);
  document.documentElement.lang = "";
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("locale detection", () => {
  it("defaults to English", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("en");
  });

  it("picks up a supported browser language", () => {
    setLanguages(["es-ES"]);

    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("es");
  });

  it("walks the browser's preference list", () => {
    // fr is unsupported, so the next entry should win.
    setLanguages(["fr-FR", "es-MX"]);

    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("es");
  });

  it("falls back to English when nothing is supported", () => {
    setLanguages(["fr-FR", "de-DE"]);

    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("en");
  });

  it("prefers a stored preference over the browser language", () => {
    localStorage.setItem(STORAGE_KEY, "es");
    setLanguages(["en-US"]);

    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("es");
  });

  it("ignores an unsupported stored value", () => {
    localStorage.setItem(STORAGE_KEY, "klingon");

    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.locale).toBe("en");
  });
});

describe("setLocale", () => {
  it("switches the active locale", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("es"));

    expect(result.current.locale).toBe("es");
  });

  it("persists the choice", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("es"));

    expect(localStorage.getItem(STORAGE_KEY)).toBe("es");
  });

  it("ignores an unsupported locale", () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("klingon"));

    expect(result.current.locale).toBe("en");
  });

  it("keeps working when localStorage throws", () => {
    // Safari in private mode.
    vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });

    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("es"));

    expect(result.current.locale).toBe("es");
  });

  it("updates <html lang>", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(document.documentElement.lang).toBe("en");

    act(() => result.current.setLocale("es"));

    expect(document.documentElement.lang).toBe("es");
  });
});

describe("t()", () => {
  it("resolves in the active locale", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    expect(result.current.t("common.retry")).toBe("Retry");

    act(() => result.current.setLocale("es"));

    expect(result.current.t("common.retry")).toBe("Reintentar");
  });

  it("falls back to English for a key the locale lacks", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("es"));

    // notifications.unread is deliberately absent from the Spanish catalogue.
    expect(result.current.t("notifications.unread", { count: 3 })).toBe("3 unread notifications");
  });

  it("pluralises in the active locale", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    act(() => result.current.setLocale("es"));

    expect(result.current.t("projects.count", { count: 1 })).toBe("1 proyecto");
    expect(result.current.t("projects.count", { count: 4 })).toBe("4 proyectos");
  });
});

describe("formatting helpers", () => {
  it("follow the active locale", () => {
    const { result } = renderHook(() => useTranslation(), { wrapper });

    const inEnglish = result.current.formatRelativeTime(
      new Date("2026-08-03T10:00:00Z"),
      new Date("2026-08-03T12:00:00Z"),
    );
    expect(inEnglish).toBe("2 hours ago");

    act(() => result.current.setLocale("es"));

    const inSpanish = result.current.formatRelativeTime(
      new Date("2026-08-03T10:00:00Z"),
      new Date("2026-08-03T12:00:00Z"),
    );
    expect(inSpanish).toBe("hace 2 horas");
  });
});

describe("useTranslation outside a provider", () => {
  it("throws rather than silently defaulting to English", () => {
    // Quietly working in English would hide the wiring bug until a
    // non-English user reported it.
    vi.spyOn(console, "error").mockImplementation(() => {});

    function Bare() {
      useTranslation();
      return null;
    }

    expect(() => render(<Bare />)).toThrow(/must be used within an I18nProvider/);
  });
});

describe("translated components", () => {
  // The error pages themselves render a TanStack <Link>, which needs a router
  // in context; exercising them here would be a router test wearing an i18n
  // costume. LanguageSwitcher has no router dependency and covers the same
  // ground: a real component reading from the provider.
  it("labels the switcher in the active locale", () => {
    localStorage.setItem(STORAGE_KEY, "es");

    render(
      <I18nProvider>
        <LanguageSwitcher />
      </I18nProvider>,
    );

    expect(screen.getByLabelText("Cambiar idioma")).toBeInTheDocument();
  });

  it("shows each language in its own name", () => {
    render(
      <I18nProvider>
        <LanguageSwitcher />
      </I18nProvider>,
    );

    // The trigger reflects the selected value; "English" is the native name
    // for `en`, which is what a user scanning the list would look for.
    expect(screen.getByLabelText("Change language")).toHaveTextContent("English");
  });
});
