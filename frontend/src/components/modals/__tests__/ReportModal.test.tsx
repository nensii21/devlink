import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ReportModal } from "../ReportModal";
import { reportsApi } from "@/api/modules/reports";

vi.mock("@/api/modules/reports", () => ({
  reportsApi: {
    reportProfile: vi.fn(),
    reportPost: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("ReportModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders profile report modal and submits report", async () => {
    (reportsApi.reportProfile as any).mockResolvedValue({
      id: "rep-1",
      status: "pending",
    });

    const handleClose = vi.fn();

    render(
      <ReportModal
        isOpen={true}
        onClose={handleClose}
        targetId="user-123"
        targetType="user"
        targetName="Bad User"
      />
    );

    expect(screen.getByText(/Report Profile/i)).toBeInTheDocument();
    expect(screen.getByText(/Bad User/i)).toBeInTheDocument();

    const submitBtn = screen.getByText(/Submit Report/i);
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(reportsApi.reportProfile).toHaveBeenCalledWith(
        "user-123",
        expect.objectContaining({
          reason: "Spam / Misleading",
        })
      );
      expect(handleClose).toHaveBeenCalled();
    });
  });

  it("submits post report with selected reason", async () => {
    (reportsApi.reportPost as any).mockResolvedValue({
      id: "rep-2",
      status: "pending",
    });

    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        targetId="post-456"
        targetType="post"
      />
    );

    const harassmentOption = screen.getByText(/Harassment or Bullying/i);
    fireEvent.click(harassmentOption);

    const submitBtn = screen.getByText(/Submit Report/i);
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(reportsApi.reportPost).toHaveBeenCalledWith(
        "post-456",
        expect.objectContaining({
          reason: "Harassment or Bullying",
          post_id: "post-456",
        })
      );
    });
  });
});
