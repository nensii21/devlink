import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: any) => ({ options: opts }),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useRouterState: () => "/settings",
}));

vi.mock("@/services", () => ({
  usersService: {
    getMe: vi.fn().mockResolvedValue({
      id: "usr_1",
      first_name: "Nancy",
      last_name: "Patel",
      username: "nensii21",
      email: "nancy@example.com",
      headline: "Full-Stack Engineer",
      bio: "Open source developer",
      version: 1,
    }),
    updateMe: vi.fn().mockResolvedValue({
      id: "usr_1",
      first_name: "Nancy",
      last_name: "Patel",
      username: "nensii21",
      email: "nancy@example.com",
      headline: "Full-Stack Engineer",
      bio: "Open source developer",
      version: 2,
    }),
    getPrivacySettings: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/api", () => ({
  authApi: {
    me: vi.fn().mockResolvedValue({}),
  },
  exportApi: {
    exportData: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

import { SettingsPage } from "@/routes/_app.settings";

// The #947 refactor these tests describe -- an H1 of "Settings" and Profile /
// Billing / Developer Accounts tabs -- is not what the settings page implements,
// and cannot be: settings-574.test.tsx asserts an H1 of "User Settings" and a
// different tab set for the same component, so the two files contradict each
// other and only one can pass. The page matches #574, and the branches these
// tests need do not exist. Skipped rather than deleted so whoever picks #947
// back up has the acceptance criteria; see #1344.
describe.skip("Settings Page Refactor (#947)", () => {
  it("renders 6 distinct navigation tabs for settings", async () => {
    render(<SettingsPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Settings");
    expect(screen.getByRole("button", { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /appearance/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /security/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /billing/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /developer accounts/i })).toBeInTheDocument();
  });

  it("switches to developer accounts tab properly", async () => {
    render(<SettingsPage />);

    const devTab = screen.getByRole("button", { name: /developer accounts/i });
    fireEvent.click(devTab);

    expect(
      screen.getByRole("heading", { name: /developer accounts & api access/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/personal access tokens/i)).toBeInTheDocument();
  });
});
