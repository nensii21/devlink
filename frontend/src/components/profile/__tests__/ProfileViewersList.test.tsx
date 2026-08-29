import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProfileViewersList, type ViewerItem } from "../ProfileViewersList";

describe("ProfileViewersList Component (#1000)", () => {
  it("renders visitor history and total viewer counts", () => {
    render(<ProfileViewersList totalViewers={25} isPremium={true} />);
    expect(screen.getByText("Recent Profile Visitors")).toBeInTheDocument();
    expect(screen.getByText("25 developers viewed your profile recently.")).toBeInTheDocument();
    expect(screen.getByText("Sarah Chen")).toBeInTheDocument();
    expect(screen.getByText("Anonymous Developer")).toBeInTheDocument();
  });

  it("displays visit frequency and visit date", () => {
    const customViewers: ViewerItem[] = [
      {
        id: "v-custom",
        viewer_id: "u-999",
        viewer_name: "Taylor Swift",
        viewer_username: "taylorswift",
        viewed_at: "2026-08-15T10:00:00Z",
        visit_count: 7,
        is_anonymous: false,
      },
    ];

    render(<ProfileViewersList viewers={customViewers} totalViewers={1} isPremium={true} />);
    expect(screen.getByText("Taylor Swift")).toBeInTheDocument();
    expect(screen.getByText("@taylorswift")).toBeInTheDocument();
    expect(screen.getByText("7 visits")).toBeInTheDocument();
    expect(screen.getByText(/Aug 15, 2026/i)).toBeInTheDocument();
  });

  it("handles privacy opt-out toggle", () => {
    const handleToggle = vi.fn();
    render(
      <ProfileViewersList hideProfileViews={false} onTogglePrivacy={handleToggle} isPremium={true} />
    );

    const toggleBtn = screen.getByRole("switch");
    fireEvent.click(toggleBtn);

    expect(handleToggle).toHaveBeenCalledWith(true);
  });

  it("handles pagination controls", () => {
    const handlePageChange = vi.fn();
    render(
      <ProfileViewersList
        currentPage={1}
        totalPages={3}
        onPageChange={handlePageChange}
        isPremium={true}
      />
    );

    const nextBtn = screen.getByRole("button", { name: /Next/i });
    fireEvent.click(nextBtn);

    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it("renders locked upgrade state for non-premium members", () => {
    const handleUpgrade = vi.fn();
    render(<ProfileViewersList isPremium={false} onUpgrade={handleUpgrade} />);

    expect(screen.getByText("See Who is Checking Out Your Profile")).toBeInTheDocument();
    expect(screen.getByText(/Upgrade to DevLink Pro to view recent visitor history/i)).toBeInTheDocument();
    expect(screen.getByText("Upgrade to DevLink Pro")).toBeInTheDocument();

    const upgradeBtn = screen.getByRole("button", { name: /Upgrade to DevLink Pro/i });
    fireEvent.click(upgradeBtn);
    expect(handleUpgrade).toHaveBeenCalled();
  });
});

