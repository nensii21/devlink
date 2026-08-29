import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SocialProofSection } from "../SocialProofSection";
import { analyticsApi } from "@/api";

vi.mock("@/api", () => ({
  analyticsApi: {
    socialProof: vi.fn(),
  },
}));

// Mock IntersectionObserver for JSDOM
class MockIntersectionObserver {
  callback: (entries: Array<{ isIntersecting: boolean }>) => void;
  constructor(callback: (entries: Array<{ isIntersecting: boolean }>) => void) {
    this.callback = callback;
  }
  observe() {
    this.callback([{ isIntersecting: true }]);
  }
  unobserve() {}
  disconnect() {}
}

beforeEach(() => {
  window.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver;
});

describe("SocialProofSection Component (#761)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <SocialProofSection />
      </QueryClientProvider>,
    );

  it("renders header badge, title, and all 5 platform growth metric categories", async () => {
    vi.mocked(analyticsApi.socialProof).mockResolvedValueOnce({
      developers: 25000,
      projects: 5400,
      teams: 3100,
      organizations: 450,
      hackathons: 180,
      last_updated: "2026-08-19T00:00:00Z",
    });

    renderComponent();

    // Verify header and badge
    expect(screen.getByText("Platform Adoption & Growth")).toBeInTheDocument();
    expect(screen.getByText("Trusted by Builders Across the Globe")).toBeInTheDocument();

    // Verify all 5 requirement metric cards
    expect(screen.getByText("Developers")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Teams")).toBeInTheDocument();
    expect(screen.getByText("Organizations")).toBeInTheDocument();
    expect(screen.getByText("Hackathons")).toBeInTheDocument();

    // Verify subtitles
    expect(screen.getByText("Active builders & engineers")).toBeInTheDocument();
    expect(screen.getByText("Open source & team builds")).toBeInTheDocument();
    expect(screen.getByText("Collaborative squads formed")).toBeInTheDocument();
    expect(screen.getByText("Startups & tech communities")).toBeInTheDocument();
    expect(screen.getByText("Events & competitions")).toBeInTheDocument();

    // Verify trends
    expect(screen.getByText("+140% this quarter")).toBeInTheDocument();
    expect(screen.getByText("850+ shipped")).toBeInTheDocument();
    expect(screen.getByText("94% match rate")).toBeInTheDocument();
    expect(screen.getByText("Global presence")).toBeInTheDocument();
    expect(screen.getByText("$150k+ prizes won")).toBeInTheDocument();
  });

  it("gracefully falls back to baseline figures if API errors", async () => {
    vi.mocked(analyticsApi.socialProof).mockRejectedValueOnce(new Error("Network Error"));

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText("Developers")).toBeInTheDocument();
      expect(screen.getByText("Projects")).toBeInTheDocument();
      expect(screen.getByText("Teams")).toBeInTheDocument();
      expect(screen.getByText("Organizations")).toBeInTheDocument();
      expect(screen.getByText("Hackathons")).toBeInTheDocument();
    });
  });
});
