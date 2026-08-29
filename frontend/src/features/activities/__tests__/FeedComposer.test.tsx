import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FeedComposer } from "../components/FeedComposer";
import { TrendingSidebar, DEFAULT_TRENDING_TOPICS } from "../components/TrendingSidebar";
import { SuggestedBuildersSidebar, DEFAULT_SUGGESTED_BUILDERS } from "../components/SuggestedBuildersSidebar";
import { postsApi } from "@/api/modules/posts";

vi.mock("@/api/modules/posts", () => ({
  postsApi: {
    create: vi.fn(),
  },
}));

describe("Redesign Builder Feed Composer (#943)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const renderComposer = (props = {}) =>
    render(
      <QueryClientProvider client={queryClient}>
        <FeedComposer {...props} />
      </QueryClientProvider>
    );

  it("renders trigger card with avatar and quick action triggers", () => {
    renderComposer({ userName: "Test Builder" });

    expect(
      screen.getByRole("button", { name: /start a post, share a project, or create a poll/i })
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /^media$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^repository$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^project$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^poll$/i })).toBeInTheDocument();
  });

  it("opens LinkedIn-style composer modal when clicking trigger or action buttons", async () => {
    renderComposer();

    const triggerBtn = screen.getByRole("button", {
      name: /start a post, share a project, or create a poll/i,
    });
    fireEvent.click(triggerBtn);

    expect(screen.getByText("Create Post")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/what do you want to share with the builder community/i)
    ).toBeInTheDocument();
  });

  it("supports markdown formatting toolbar (bold, italic, code, quote)", async () => {
    renderComposer();

    fireEvent.click(
      screen.getByRole("button", {
        name: /start a post, share a project, or create a poll/i,
      })
    );

    const textarea = screen.getByPlaceholderText(
      /what do you want to share with the builder community/i
    ) as HTMLTextAreaElement;

    const boldBtn = screen.getByTitle("Bold");
    fireEvent.click(boldBtn);

    expect(textarea.value).toContain("**text**");
  });

  it("allows attaching a repository and submitting the post", async () => {
    vi.mocked(postsApi.create).mockResolvedValueOnce({} as any);

    renderComposer();

    // Click trigger
    fireEvent.click(
      screen.getByRole("button", {
        name: /start a post, share a project, or create a poll/i,
      })
    );

    const textarea = screen.getByPlaceholderText(
      /what do you want to share with the builder community/i
    );
    fireEvent.change(textarea, { target: { value: "Check out our core repo!" } });

    // Open repo picker
    const repoBtn = screen.getByTitle("Attach Repository");
    fireEvent.click(repoBtn);

    const selectRepoBtn = screen.getByText("devlink/core");
    fireEvent.click(selectRepoBtn);

    expect(screen.getByText("devlink/core")).toBeInTheDocument();

    const postBtn = screen.getByRole("button", { name: /post/i });
    fireEvent.click(postBtn);

    await waitFor(() => {
      expect(postsApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          content: "Check out our core repo!",
          repository: expect.objectContaining({ name: "devlink/core" }),
        })
      );
    });
  });

  it("renders TrendingSidebar and handles topic clicks", () => {
    const handleSelect = vi.fn();
    render(<TrendingSidebar onSelectTopic={handleSelect} />);

    expect(screen.getByText("Trending Topics")).toBeInTheDocument();
    expect(screen.getByText("React19")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();

    fireEvent.click(screen.getByText("React19"));
    expect(handleSelect).toHaveBeenCalledWith("React19");
  });

  it("renders SuggestedBuildersSidebar and toggles follow state", () => {
    render(<SuggestedBuildersSidebar />);

    expect(screen.getByText("Suggested Builders")).toBeInTheDocument();
    expect(screen.getByText("Alex Rivera")).toBeInTheDocument();

    const followButtons = screen.getAllByRole("button", { name: /follow/i });
    expect(followButtons.length).toBeGreaterThan(0);

    fireEvent.click(followButtons[0]);
    expect(screen.getByText("Following")).toBeInTheDocument();
  });
});
