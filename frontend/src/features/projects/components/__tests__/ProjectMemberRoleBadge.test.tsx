import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ProjectMemberRoleBadge } from "../ProjectMemberRoleBadge";

describe("ProjectMemberRoleBadge Component", () => {
  it("renders Project Owner badge correctly for owner role", () => {
    render(<ProjectMemberRoleBadge role="owner" />);
    expect(screen.getByText("Project Owner")).toBeInTheDocument();
  });

  it("renders Maintainer badge correctly for maintainer role", () => {
    render(<ProjectMemberRoleBadge role="maintainer" />);
    expect(screen.getByText("Maintainer")).toBeInTheDocument();
  });

  it("renders Contributor badge correctly for contributor role", () => {
    render(<ProjectMemberRoleBadge role="contributor" />);
    expect(screen.getByText("Contributor")).toBeInTheDocument();
  });

  it("renders Reviewer badge correctly for reviewer role", () => {
    render(<ProjectMemberRoleBadge role="reviewer" />);
    expect(screen.getByText("Reviewer")).toBeInTheDocument();
  });

  it("renders Viewer badge correctly for viewer role", () => {
    render(<ProjectMemberRoleBadge role="viewer" />);
    expect(screen.getByText("Viewer")).toBeInTheDocument();
  });
});
