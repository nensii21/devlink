import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AnnouncementBanner, type Announcement } from "../shared/AnnouncementBanner";
import { api } from "../../api/client";

const REAL_ANNOUNCEMENT: Announcement = {
  id: "ann-real",
  title: "Read receipts are live",
  content: "Message read receipts have shipped for all conversations.",
  severity: "info",
  target_audience: "all",
  start_date: "2026-08-20T00:00:00Z",
  is_active: true,
};

function renderBanner() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AnnouncementBanner />
    </QueryClientProvider>,
  );
}

describe("AnnouncementBanner", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the announcements the backend returned", async () => {
    vi.spyOn(api, "get").mockResolvedValue([REAL_ANNOUNCEMENT] as never);

    renderBanner();

    expect(await screen.findByText(/Read receipts are live/)).toBeInTheDocument();
  });

  // The regression, and the worst of the three: this did not need a failure.
  // An empty list is a valid answer meaning "nothing to announce", and it was
  // treated as one, so every user with no announcements was shown a hardcoded
  // "Scheduled Maintenance tonight from 2:00 AM to 3:00 AM UTC" -- dated
  // new Date(), so always tonight, on every page, forever.
  it("renders nothing when there are no announcements", async () => {
    vi.spyOn(api, "get").mockResolvedValue([] as never);

    const { container } = renderBanner();

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByText(/Scheduled Maintenance/i)).not.toBeInTheDocument();
  });

  it("renders nothing when the request fails", async () => {
    vi.spyOn(api, "get").mockRejectedValue(new Error("500"));

    const { container } = renderBanner();

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(screen.queryByText(/Scheduled Maintenance/i)).not.toBeInTheDocument();
    expect(container).toBeEmptyDOMElement();
  });

  // The mock was also the useQuery default value, so it painted before any
  // request resolved -- a user saw the fake banner on first load even when the
  // backend was about to answer with nothing.
  it("renders nothing while the request is still in flight", () => {
    vi.spyOn(api, "get").mockReturnValue(new Promise(() => {}) as never);

    const { container } = renderBanner();

    expect(container).toBeEmptyDOMElement();
  });

  it("hides an announcement once it is dismissed", async () => {
    vi.spyOn(api, "get").mockResolvedValue([REAL_ANNOUNCEMENT] as never);

    renderBanner();
    await screen.findByText(/Read receipts are live/);

    await userEvent.click(screen.getByRole("button", { name: /dismiss banner/i }));

    await waitFor(() =>
      expect(screen.queryByText(/Read receipts are live/)).not.toBeInTheDocument(),
    );
  });

  it("keeps a dismissal across a remount", async () => {
    vi.spyOn(api, "get").mockResolvedValue([REAL_ANNOUNCEMENT] as never);

    const first = renderBanner();
    await screen.findByText(/Read receipts are live/);
    await userEvent.click(screen.getByRole("button", { name: /dismiss banner/i }));
    first.unmount();

    const { container } = renderBanner();

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("still shows a different announcement after one is dismissed", async () => {
    vi.spyOn(api, "get").mockResolvedValue([REAL_ANNOUNCEMENT] as never);

    const first = renderBanner();
    await screen.findByText(/Read receipts are live/);
    await userEvent.click(screen.getByRole("button", { name: /dismiss banner/i }));
    first.unmount();

    vi.spyOn(api, "get").mockResolvedValue([
      { ...REAL_ANNOUNCEMENT, id: "ann-other", title: "Planned downtime" },
    ] as never);

    renderBanner();

    expect(await screen.findByText(/Planned downtime/)).toBeInTheDocument();
  });
});
