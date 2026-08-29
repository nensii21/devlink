import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApplyModal } from "../ApplyModal";
import { getProjectBuilderFlares } from "@/lib/api";
import { useApplyToFlare } from "@/hooks/useApplications";

vi.mock("@/lib/api", () => ({
  getProjectBuilderFlares: vi.fn(),
}));

vi.mock("@/hooks/useApplications", () => ({
  useApplyToFlare: vi.fn(),
}));

describe("ApplyToProject Modal Component (#968)", () => {
  let queryClient: QueryClient;
  const mockMutateAsync = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();

    vi.mocked(useApplyToFlare).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);
  });

  const renderModal = (isOpen = true, projectId = "proj-123") =>
    render(
      <QueryClientProvider client={queryClient}>
        <ApplyModal isOpen={isOpen} onClose={vi.fn()} projectId={projectId} />
      </QueryClientProvider>
    );

  it("renders role selection, short introduction, portfolio, github, and resume upload fields", async () => {
    vi.mocked(getProjectBuilderFlares).mockResolvedValueOnce([
      {
        id: "flare-1",
        role: "Frontend Engineer",
        title: "React Lead",
        status: "open",
        project_id: "proj-123",
      },
    ] as any);

    renderModal();

    await waitFor(() => {
      expect(screen.queryByText("Loading roles...")).not.toBeInTheDocument();
    });

    expect(screen.getByText("Apply to Project")).toBeInTheDocument();
    expect(screen.getByText(/frontend engineer - react lead/i)).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/why are you a great fit for this role/i)
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/https:\/\/your-portfolio.com/i)
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/https:\/\/github.com\/username/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/upload resume/i)).toBeInTheDocument();
  });

  it("submits application payload with intro, selected role, portfolio, github, and resume file", async () => {
    vi.mocked(getProjectBuilderFlares).mockResolvedValueOnce([
      {
        id: "flare-1",
        role: "Frontend Engineer",
        title: "React Lead",
        status: "open",
        project_id: "proj-123",
      },
    ] as any);

    mockMutateAsync.mockResolvedValueOnce({});

    renderModal();

    await waitFor(() => {
      expect(screen.queryByText("Loading roles...")).not.toBeInTheDocument();
    });

    expect(screen.getByText("Apply to Project")).toBeInTheDocument();

    // Fill form
    const introInput = screen.getByPlaceholderText(/why are you a great fit for this role/i);
    const portfolioInput = screen.getByPlaceholderText(/https:\/\/your-portfolio.com/i);
    const githubInput = screen.getByPlaceholderText(/https:\/\/github.com\/username/i);

    fireEvent.change(introInput, { target: { value: "Experienced React developer with 4 years experience." } });
    fireEvent.change(portfolioInput, { target: { value: "https://sarahdev.io" } });
    fireEvent.change(githubInput, { target: { value: "https://github.com/sarahchen" } });

    const submitBtn = screen.getByRole("button", { name: /submit application/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          projectId: "proj-123",
          flareId: "flare-1",
          message: "Experienced React developer with 4 years experience.",
          portfolioUrl: "https://sarahdev.io",
          githubUrl: "https://github.com/sarahchen",
        })
      );
    });
  });

  it("displays alert message when no open roles exist for project", async () => {
    vi.mocked(getProjectBuilderFlares).mockResolvedValueOnce([]);

    renderModal();

    await waitFor(() => {
      expect(screen.getByText("No Open Roles")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/this project is currently not accepting new applications/i)
    ).toBeInTheDocument();
  });
});
