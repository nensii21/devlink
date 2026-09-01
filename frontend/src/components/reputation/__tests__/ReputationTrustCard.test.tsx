import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TrustScoreBadge } from "../TrustScoreBadge";
import { ReputationTrustCard } from "../ReputationTrustCard";

describe("Trust & Reputation Score Components (#970)", () => {
  it("renders TrustScoreBadge correctly with normalized score and verification indicator", () => {
    render(
      <TrustScoreBadge
        trustScore={85}
        trustLevel="Highly Trusted Member ⭐"
        isVerified={true}
      />
    );

    expect(screen.getByText(/Trust Score: 85%/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Verified Developer Account/i)).toBeInTheDocument();
  });

  it("renders ReputationTrustCard with score breakdown across criteria", () => {
    render(
      <ReputationTrustCard
        username="Alex Chen"
        reputationScore={350}
        trustScore={70}
        trustLevel="Verified Contributor 🛡️"
        isVerified={true}
        breakdown={{
          collaborations_points: 60,
          pull_requests_points: 100,
          completed_projects_points: 100,
          feedback_points: 20,
          endorsements_points: 30,
          verification_points: 40,
        }}
      />
    );

    expect(screen.getByText(/Reputation & Trust Score/i)).toBeInTheDocument();
    expect(screen.getAllByText(/70%/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/350/i)).toBeInTheDocument();
    expect(screen.getByText(/Successful Collaborations/i)).toBeInTheDocument();
    expect(screen.getByText(/Merged Pull Requests/i)).toBeInTheDocument();
    expect(screen.getByText(/Completed Projects/i)).toBeInTheDocument();
  });

  it("triggers peer endorsement flow when Endorse Builder button is clicked", async () => {
    const handleEndorse = vi.fn().mockResolvedValue(undefined);

    render(
      <ReputationTrustCard
        username="Jane Doe"
        isSelf={false}
        onEndorse={handleEndorse}
      />
    );

    const endorseBtn = screen.getByRole("button", { name: /Endorse Builder/i });
    fireEvent.click(endorseBtn);

    expect(screen.getByText(/Endorse Jane Doe/i)).toBeInTheDocument();

    const skillInput = screen.getByPlaceholderText(/e.g. React, System Architecture/i);
    fireEvent.change(skillInput, { target: { value: "FastAPI Backend" } });

    const submitBtn = screen.getByRole("button", { name: /Submit Endorsement/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleEndorse).toHaveBeenCalledWith("FastAPI Backend", undefined);
    });
  });
});
