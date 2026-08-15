import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CollaborationStatusBadge } from "@/features/collaboration/components/CollaborationStatusBadge";
import {
  COLLABORATION_STATUSES,
  getCollaborationStatusOption,
} from "@/features/collaboration/types";

describe("CollaborationStatusBadge", () => {
  it("renders the label for a known status", () => {
    render(<CollaborationStatusBadge status="coding" />);
    expect(screen.getByText("Coding")).toBeInTheDocument();
  });

  it("renders a label for each supported status", () => {
    const cases = [
      ["coding", "Coding"],
      ["reviewing_pr", "Reviewing PR"],
      ["in_meeting", "In meeting"],
      ["looking_for_project", "Looking for project"],
      ["available", "Available now"],
    ] as const;
    for (const [status, label] of cases) {
      const { unmount } = render(<CollaborationStatusBadge status={status} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    }
  });

  it("falls back to 'Available now' for unknown or missing status", () => {
    render(<CollaborationStatusBadge status="not_a_status" />);
    expect(screen.getByText("Available now")).toBeInTheDocument();
  });

  it("hides the visible label but keeps it accessible when showLabel is false", () => {
    render(<CollaborationStatusBadge status="coding" showLabel={false} />);
    expect(screen.getByText("Coding", { selector: ".sr-only" })).toBeInTheDocument();
    expect(screen.getByText("Coding")).toHaveClass("sr-only");
  });

  it("applies the status-specific accent classes", () => {
    render(<CollaborationStatusBadge status="coding" />);
    const badge = screen.getByTitle("Currently writing code");
    expect(badge.className).toContain("violet");
  });
});

describe("getCollaborationStatusOption", () => {
  it("returns the matching option for a known value", () => {
    expect(getCollaborationStatusOption("coding")).toMatchObject({
      value: "coding",
      label: "Coding",
    });
  });

  it("returns the available option for unknown values", () => {
    expect(getCollaborationStatusOption("bogus")).toMatchObject({
      value: "available",
    });
  });

  it("returns the available option for null/undefined", () => {
    expect(getCollaborationStatusOption(undefined)).toMatchObject({
      value: "available",
    });
    expect(getCollaborationStatusOption(null)).toMatchObject({
      value: "available",
    });
  });

  it("exposes every supported status with an icon", () => {
    for (const option of COLLABORATION_STATUSES) {
      expect(option.icon).toBeDefined();
      expect(option.label).toBeTruthy();
    }
  });
});
