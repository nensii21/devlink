import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApplicationsList } from "../ApplicationsList";
import { getProjectApplications } from "@/lib/api";
import {
  useAcceptApplication,
  useRejectApplication,
  useWithdrawApplication,
} from "@/hooks/useApplications";

vi.mock("@/lib/api", () => ({
  getProjectApplications: vi.fn(),
}));

vi.mock("@/hooks/useApplications", () => ({
  useAcceptApplication: vi.fn(),
  useRejectApplication: vi.fn(),
  useWithdrawApplication: vi.fn(),
}));

describe("ApplicationsList Component (#968)", () => {
  let queryClient: QueryClient;
  const mockWithdrawMutateAsync = vi.fn();
  const mockAcceptMutateAsync = vi.fn();
  const mockRejectMutateAsync = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();

    vi.mocked(useWithdrawApplication).mockReturnValue({
      mutate: mockWithdrawMutateAsync,
      mutateAsync: mockWithdrawMutateAsync,
      isPending: false,
    } as any);

    vi.mocked(useAcceptApplication).mockReturnValue({
      mutateAsync: mockAcceptMutateAsync,
      isPending: false,
    } as any);

    vi.mocked(useRejectApplication).mockReturnValue({
      mutateAsync: mockRejectMutateAsync,
      isPending: false,
    } as any);
  });

  const renderList = (projectId = "proj-123") =>
    render(
      <QueryClientProvider client={queryClient}>
        <ApplicationsList projectId={projectId} />
      </QueryClientProvider>
    );

  it("renders applicant status badges (pending, accepted, rejected, withdrawn)", async () => {
    vi.mocked(getProjectApplications).mockResolvedValueOnce([
      {
        id: "app-1",
        project_id: "proj-123",
        flare_id: "flare-1",
        user_id: "user-1",
        status: "pending",
        message: "Excited to join!",
        portfolio_url: "https://portfolio.com",
        github_url: "https://github.com/user1",
        created_at: "2026-08-20T00:00:00Z",
      },
      {
        id: "app-2",
        project_id: "proj-123",
        flare_id: "flare-2",
        user_id: "user-2",
        status: "accepted",
        message: "Ready to contribute.",
        created_at: "2026-08-21T00:00:00Z",
      },
      {
        id: "app-3",
        project_id: "proj-123",
        flare_id: "flare-3",
        user_id: "user-3",
        status: "withdrawn",
        message: "Withdrawing application.",
        created_at: "2026-08-22T00:00:00Z",
      },
    ] as any);

    renderList();

    await waitFor(() => {
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/accepted/i)).toBeInTheDocument();
    expect(screen.getByText(/withdrawn/i)).toBeInTheDocument();
    expect(screen.getByText("Excited to join!")).toBeInTheDocument();
  });

  it("handles withdraw application button action", async () => {
    vi.mocked(getProjectApplications).mockResolvedValueOnce([
      {
        id: "app-10",
        project_id: "proj-123",
        flare_id: "flare-1",
        user_id: "user-10",
        status: "pending",
        message: "Application to withdraw",
        created_at: "2026-08-20T00:00:00Z",
      },
    ] as any);

    mockWithdrawMutateAsync.mockResolvedValueOnce({});

    renderList();

    await waitFor(() => {
      expect(screen.getByText("Application to withdraw")).toBeInTheDocument();
    });

    const withdrawBtn = screen.getByRole("button", { name: /withdraw/i });
    fireEvent.click(withdrawBtn);

    await waitFor(() => {
      expect(mockWithdrawMutateAsync).toHaveBeenCalledWith("app-10");
    });
  });
});
