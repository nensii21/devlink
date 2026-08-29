import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: any) => ({
    ...opts,
    options: opts,
    useParams: () => ({ username: "nancy_dev" }),
  }),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useRouterState: () => "/profile/nancy_dev",
  useParams: () => ({ username: "nancy_dev" }),
  useNavigate: () => vi.fn(),
  notFound: () => new Error("Not found"),
}));

vi.mock("@tanstack/react-query", () => ({
  useMutation: () => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  }),
  useQuery: () => ({
    data: null,
    isLoading: false,
  }),
}));

vi.mock("@/hooks/useFollow", () => ({
  useFollowStatus: () => ({ data: { follower_count: 42, following_count: 18 } }),
}));

vi.mock("@/hooks/useCollaborationStatus", () => ({
  useCollaborationStatus: () => ({
    status: "available",
    setStatus: vi.fn(),
    isLoading: false,
  }),
}));

import { ProfilePage } from "@/routes/_app.profile.$username";

describe("Expand User Profiles with Professional Networking (#948)", () => {
  it("renders all professional networking components and profile fields", () => {
    render(<ProfilePage />);

    // 1. Headline
    expect(
      screen.getByText(/Senior Full Stack Engineer • Open Source Enthusiast • React & FastAPI/i),
    ).toBeInTheDocument();

    // 2. Open to Work badge
    expect(screen.getByText(/Open to Work/i)).toBeInTheDocument();

    // 3. Availability
    expect(screen.getByText(/Availability:/i)).toBeInTheDocument();
    expect(screen.getByText(/Immediate \(Full-time & Remote\)/i)).toBeInTheDocument();

    // 4. Website
    expect(screen.getByText(/devlink.io\/alex/i)).toBeInTheDocument();

    // 5. Experience Section
    expect(screen.getByRole("heading", { name: /experience/i })).toBeInTheDocument();

    // 6. Education Section
    expect(screen.getByRole("heading", { name: /education/i })).toBeInTheDocument();
    expect(screen.getByText(/University of California, Berkeley/i)).toBeInTheDocument();

    // 7. Certifications Section
    expect(
      screen.getByRole("heading", { name: /certifications & licenses/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/AWS Certified Solutions Architect – Professional/i),
    ).toBeInTheDocument();

    // 8. Skills Section
    expect(
      screen.getByRole("heading", { name: /developer skill matrix/i }),
    ).toBeInTheDocument();

    // 9. Featured Repositories Section
    expect(screen.getByRole("heading", { name: /featured repositories/i })).toBeInTheDocument();
    expect(screen.getByText(/devlink-core/i)).toBeInTheDocument();

    // 10. Portfolio & Showcase Section
    expect(screen.getByRole("heading", { name: /portfolio & highlights/i })).toBeInTheDocument();
    expect(screen.getByText(/DevLink Collaboration Platform/i)).toBeInTheDocument();
  });
});
