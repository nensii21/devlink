import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GreetingHero } from "../GreetingHero";
import { StatsRow } from "../StatsRow";
import {
  CurrentProjects,
  AISuggestions,
  QuickActions,
  RecentActivity,
  Upcoming,
  CompactMessagingWidget,
  NotificationsWidget,
  UpcomingEventsWidget,
  UpgradePlanCTA,
} from "../sections";
import { CustomizeDashboardToolbar } from "../CustomizeDashboardToolbar";
import { WidgetConfigModal } from "../WidgetConfigModal";
import { DEFAULT_WIDGET_LAYOUTS } from "../dashboardWidgets";

// Mocks
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={typeof to === "string" ? to : "#"} {...props}>
      {children}
    </a>
  ),
  createFileRoute: () => () => ({ component: () => null }),
}));

vi.mock("@/services", () => ({
  projectsService: {
    list: vi.fn().mockResolvedValue([]),
  },
  messagesService: {
    conversations: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock("@/api", () => ({
  recommendationsApi: {
    builders: vi.fn().mockResolvedValue({ results: [] }),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("Dashboard Typography Standardization (#747)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Heading Hierarchy & Typography Scale", () => {
    it("renders GreetingHero with standard h1 heading and subtitle caption", () => {
      render(<GreetingHero />, { wrapper: createWrapper() });

      const heading = screen.getByRole("heading", { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe("H1");
      expect(heading).toHaveClass("text-2xl", "font-bold", "tracking-tight");

      expect(
        screen.getByText("Here's what's happening with your workspace today."),
      ).toBeInTheDocument();
    });

    it("renders StatsRow with consistent typography values and labels", () => {
      render(<StatsRow />);

      expect(screen.getByText("Active Projects")).toBeInTheDocument();
      expect(screen.getByText("Team Members")).toBeInTheDocument();
      expect(screen.getByText("Unread Messages")).toBeInTheDocument();
      expect(screen.getByText("AI Score")).toBeInTheDocument();

      // Metric numbers
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("24")).toBeInTheDocument();
    });

    it("renders SectionHeader with standard h3 semantic heading in CurrentProjects", async () => {
      render(<CurrentProjects />, { wrapper: createWrapper() });

      const sectionHeading = screen.getByRole("heading", { level: 3 });
      expect(sectionHeading).toHaveTextContent("Current Projects");
      expect(await screen.findByText("DevLink Platform")).toBeInTheDocument();
      expect(await screen.findByText("AI Matching Engine")).toBeInTheDocument();
    });

    it("renders AI Recommendations with proper headings and match percentages", async () => {
      render(<AISuggestions />, { wrapper: createWrapper() });

      const sectionHeading = screen.getByRole("heading", { level: 3 });
      expect(sectionHeading).toHaveTextContent("AI Recommendations");
      expect(await screen.findByText("Rahul Verma")).toBeInTheDocument();
      expect(await screen.findByText("94% Match")).toBeInTheDocument();
    });

    it("renders QuickActions with standardized section heading and card labels", () => {
      render(<QuickActions />);

      const heading = screen.getByRole("heading", { level: 3 });
      expect(heading).toHaveTextContent("Quick Actions");

      expect(screen.getByText("Create Project")).toBeInTheDocument();
      expect(screen.getByText("Publish Flare")).toBeInTheDocument();
      expect(screen.getByText("Find Builders")).toBeInTheDocument();
      expect(screen.getByText("Messages")).toBeInTheDocument();
    });

    it("renders RecentActivity with standardized typography scale", () => {
      render(<RecentActivity />);

      const heading = screen.getByRole("heading", { level: 3 });
      expect(heading).toHaveTextContent("Recent Activity");
      expect(screen.getByText("Alex commented on DevLink Platform")).toBeInTheDocument();
      expect(screen.getByText("Sarah accepted your invitation")).toBeInTheDocument();
    });

    it("renders Upcoming and Events widgets with standardized typography", () => {
      render(
        <div>
          <Upcoming />
          <UpcomingEventsWidget />
        </div>,
      );

      expect(screen.getByRole("heading", { name: "Upcoming" })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Upcoming Events" })).toBeInTheDocument();
      expect(screen.getAllByText("Web3 Hackathon").length).toBeGreaterThan(0);
    });

    it("renders CompactMessagingWidget with standardized typography", async () => {
      render(<CompactMessagingWidget />, { wrapper: createWrapper() });

      const heading = screen.getByRole("heading", { level: 3 });
      expect(heading).toHaveTextContent("Messages");
      expect(await screen.findByText("Sarah Chen")).toBeInTheDocument();
      expect(await screen.findByText("Alex Rivera")).toBeInTheDocument();
      expect(await screen.findByText("Merged the latest PR for auth.")).toBeInTheDocument();
    });

    it("renders UpgradePlanCTA with standardized h4 card heading and caption", () => {
      render(<UpgradePlanCTA />);

      const heading = screen.getByRole("heading", { level: 4 });
      expect(heading).toHaveTextContent("Upgrade your plan");
      expect(
        screen.getByText("Unlock premium features and boost your productivity."),
      ).toBeInTheDocument();
      expect(screen.getByText("Upgrade Now")).toBeInTheDocument();
    });

    it("renders CustomizeDashboardToolbar and WidgetConfigModal with standardized typography", () => {
      render(
        <div>
          <CustomizeDashboardToolbar
            isCustomizing={true}
            isSaving={false}
            hiddenCount={0}
            onToggleCustomizing={vi.fn()}
            onOpenAddModal={vi.fn()}
            onResetLayout={vi.fn()}
            onSaveLayout={vi.fn()}
          />
          <WidgetConfigModal
            open={true}
            onOpenChange={vi.fn()}
            layouts={DEFAULT_WIDGET_LAYOUTS}
            onToggleVisibility={vi.fn()}
            onTogglePin={vi.fn()}
            onReset={vi.fn()}
          />
        </div>,
      );

      expect(screen.getByText("Customizing Dashboard Layout")).toBeInTheDocument();
      expect(screen.getByText("Customize Widgets")).toBeInTheDocument();
    });
  });
});
