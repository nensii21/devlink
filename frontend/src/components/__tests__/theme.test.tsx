/**
 * Unit tests for DevLink Theme Support system.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, renderHook, act } from "@testing-library/react";
import { ThemeProvider, useTheme } from "@/context/ThemeContext";
import { ThemeToggle } from "@/components/shared/ThemeToggle";

describe("ThemeProvider & useTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it("provides default 'system' theme when not specified", () => {
    const { result } = renderHook(() => useTheme(), {
      wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
    });
    expect(result.current.theme).toBe("system");
  });

  it("switches theme to 'dark' and adds dark class to root", () => {
    const { result } = renderHook(() => useTheme(), {
      wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
    });

    act(() => {
      result.current.setTheme("dark");
    });

    expect(result.current.theme).toBe("dark");
    expect(result.current.resolvedTheme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("devlink-theme")).toBe("dark");
  });

  it("switches theme to 'light' and removes dark class from root", () => {
    const { result } = renderHook(() => useTheme(), {
      wrapper: ({ children }) => <ThemeProvider defaultTheme="dark">{children}</ThemeProvider>,
    });

    act(() => {
      result.current.setTheme("light");
    });

    expect(result.current.theme).toBe("light");
    expect(result.current.resolvedTheme).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(localStorage.getItem("devlink-theme")).toBe("light");
  });
});

describe("ThemeToggle Component", () => {
  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it("renders light, dark, and system options", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Dark")).toBeInTheDocument();
    expect(screen.getByText("System")).toBeInTheDocument();
  });

  it("changes theme when clicking an option button", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    const darkBtn = screen.getByRole("radio", { name: /dark/i });
    fireEvent.click(darkBtn);

    expect(darkBtn).toHaveAttribute("aria-checked", "true");
    expect(localStorage.getItem("devlink-theme")).toBe("dark");
  });

  it("renders dropdown variant when specified", () => {
    render(
      <ThemeProvider>
        <ThemeToggle variant="dropdown" />
      </ThemeProvider>,
    );

    const select = screen.getByRole("combobox", { name: /select theme mode/i });
    expect(select).toBeInTheDocument();

    fireEvent.change(select, { target: { value: "dark" } });
    expect(localStorage.getItem("devlink-theme")).toBe("dark");
  });
});
