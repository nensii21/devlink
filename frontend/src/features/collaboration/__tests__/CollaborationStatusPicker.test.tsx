import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollaborationStatusPicker } from "@/features/collaboration/components/CollaborationStatusPicker";

describe("CollaborationStatusPicker", () => {
  it("renders the current status label", () => {
    render(<CollaborationStatusPicker value="coding" onChange={() => {}} />);
    expect(screen.getByRole("button")).toHaveTextContent("Coding");
  });

  it("opens the menu on click and shows all statuses", async () => {
    const user = userEvent.setup();
    render(<CollaborationStatusPicker value="available" onChange={() => {}} />);
    await user.click(screen.getByRole("button"));
    expect(await screen.findByText("Coding")).toBeInTheDocument();
    expect(screen.getByText("Reviewing PR")).toBeInTheDocument();
    expect(screen.getByText("In meeting")).toBeInTheDocument();
    expect(screen.getByText("Looking for project")).toBeInTheDocument();
    expect(screen.getAllByText("Available now").length).toBeGreaterThanOrEqual(1);
  });

  it("calls onChange with the selected status", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CollaborationStatusPicker value="available" onChange={onChange} />);
    await user.click(screen.getByRole("button"));
    await user.click(await screen.findByText("Coding"));
    expect(onChange).toHaveBeenCalledWith("coding");
  });

  it("is disabled when the disabled prop is set", () => {
    render(<CollaborationStatusPicker value="available" onChange={() => {}} disabled />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
