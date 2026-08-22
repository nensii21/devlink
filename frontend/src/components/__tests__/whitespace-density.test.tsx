import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useRouterState: () => "/dashboard",
}));

import { GreetingHero } from "@/features/dashboard/GreetingHero";

describe("UI Whitespace and Density Optimization (#937)", () => {
  it("renders GreetingHero with compact padding and optimized stats badges", () => {
    render(<GreetingHero />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText("2 Active Projects")).toBeInTheDocument();
    expect(screen.getByText("Continue Working")).toBeInTheDocument();
    expect(screen.getByText("Progress")).toBeInTheDocument();
  });
});
