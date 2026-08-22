import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkspaceStatusIndicator } from "@/components/layout/WorkspaceStatusIndicator";
import { RightPanel } from "@/components/layout/RightPanel";

describe("WorkspaceStatusIndicator and Header Integration", () => {
  it("renders compact workspace status indicator with operational state", () => {
    render(<WorkspaceStatusIndicator />);
    const trigger = screen.getByRole("button", {
      name: /workspace status/i,
    });
    expect(trigger).toBeInTheDocument();
    expect(screen.getByText("DevLink Alpha")).toBeInTheDocument();
    expect(screen.getByText("Operational")).toBeInTheDocument();
  });

  it("does not render the bulky workspace status card in RightPanel", () => {
    render(<RightPanel />);
    expect(screen.queryByText("All systems operational.")).not.toBeInTheDocument();
    expect(screen.getByText("AI Suggestions")).toBeInTheDocument();
  });
});
