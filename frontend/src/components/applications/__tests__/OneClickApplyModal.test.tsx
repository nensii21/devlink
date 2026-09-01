import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OneClickApplyModal } from "../OneClickApplyModal";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { applicationsApi } from "@/api/modules/applications";

vi.mock("@/api/modules/applications", () => ({
  applicationsApi: {
    getPrefill: vi.fn(),
    oneClickApply: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe("OneClickApplyModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (applicationsApi.getPrefill as any).mockResolvedValue({
      user_id: "user-123",
      full_name: "Test Developer",
      username: "testdev",
      headline: "Senior React Engineer",
      skills: ["React", "TypeScript"],
      github_url: "https://github.com/testdev",
      portfolio_url: "https://test.dev",
      resume_url: "https://test.dev/resume.pdf",
      role: "Frontend Developer",
      suggested_cover_letter: "Tailored cover letter text",
    });
  });

  it("renders modal and loads prefill data", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <OneClickApplyModal
          isOpen={true}
          onClose={vi.fn()}
          projectId="proj-123"
          projectTitle="DevLink Core App"
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/1-Click Application/i)).toBeInTheDocument();
      expect(screen.getByText(/Test Developer/i)).toBeInTheDocument();
      expect(screen.getByText(/Tailored cover letter text/i)).toBeInTheDocument();
    });
  });

  it("submits application on 1-click submit", async () => {
    (applicationsApi.oneClickApply as any).mockResolvedValue({
      id: "app-123",
      status: "pending",
      project_id: "proj-123",
    });

    const handleClose = vi.fn();

    render(
      <QueryClientProvider client={queryClient}>
        <OneClickApplyModal
          isOpen={true}
          onClose={handleClose}
          projectId="proj-123"
          projectTitle="DevLink Core App"
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Submit Application \(1-Click\)/i)).toBeInTheDocument();
    });

    const submitBtn = screen.getByText(/Submit Application \(1-Click\)/i);
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(applicationsApi.oneClickApply).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: "proj-123",
          auto_use_profile: true,
        })
      );
    });
  });
});
