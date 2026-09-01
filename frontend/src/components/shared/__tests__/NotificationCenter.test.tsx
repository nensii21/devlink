import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { NotificationCenter } from "../NotificationCenter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({ user: { id: "user-1", email: "test@example.com" } }),
}));

vi.mock("@/lib/api", () => ({
  default: {
    get: vi.fn().mockResolvedValue([
      {
        id: "notif-1",
        type: "mention",
        title: "Mention Notification",
        message: "You were mentioned in a comment",
        created_at: new Date().toISOString(),
        is_read: false,
      },
      {
        id: "notif-2",
        type: "application",
        title: "Application Status",
        message: "Your application was accepted",
        created_at: new Date().toISOString(),
        is_read: true,
      },
    ]),
    patch: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("NotificationCenter Component", () => {
  it("renders trigger bell button", () => {
    renderWithProviders(<NotificationCenter />);
    const button = screen.getByRole("button", { name: /notifications/i });
    expect(button).toBeInTheDocument();
  });

  it("opens popover with notification list on click", async () => {
    renderWithProviders(<NotificationCenter />);
    const button = screen.getByRole("button", { name: /notifications/i });
    fireEvent.click(button);

    expect(await screen.findByRole("heading", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("Unread")).toBeInTheDocument();
    expect(screen.getByText("Mentions")).toBeInTheDocument();
    expect(screen.getByText("Apps")).toBeInTheDocument();
  });

  it("renders notifications and filters by tab", async () => {
    renderWithProviders(<NotificationCenter />);
    const button = screen.getByRole("button", { name: /notifications/i });
    fireEvent.click(button);

    expect(await screen.findByText("Mention Notification")).toBeInTheDocument();
    expect(screen.getByText("Application Status")).toBeInTheDocument();

    const mentionsTab = screen.getByRole("tab", { name: "Mentions" });
    const user = userEvent.setup();
    await user.click(mentionsTab);

    expect(screen.getByText("Mention Notification")).toBeInTheDocument();
    expect(screen.queryByText("Application Status")).not.toBeInTheDocument();
  });
});
