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
    updateMe: vi.fn().mockResolvedValue({}),
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

import { UserSettingsPage } from "@/routes/_app.settings";

describe("Build User Settings Page (#574)", () => {
  it("renders 5 centralized settings tabs for Account, Privacy, Notifications, Appearance, Security", () => {
    render(<UserSettingsPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("User Settings");
    expect(screen.getByRole("button", { name: /^account/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /privacy/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /appearance/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /security/i })).toBeInTheDocument();
  });

  it("switches between settings tabs properly", () => {
    render(<UserSettingsPage />);

    const privacyTab = screen.getByRole("button", { name: /privacy/i });
    fireEvent.click(privacyTab);

    expect(screen.getByRole("heading", { name: /privacy & visibility/i })).toBeInTheDocument();
    expect(screen.getByText(/public profile visibility/i)).toBeInTheDocument();
  });
});
