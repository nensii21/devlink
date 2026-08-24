import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getTeamActivityTimeline } from "../modules/teamActivity";
import { api } from "../client";

const PROJECT_ID = 7;

const EMPTY_PAGE = {
  project_id: PROJECT_ID,
  items: [],
  total: 0,
  page: 1,
  limit: 10,
  has_more: false,
};

describe("getTeamActivityTimeline", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue(EMPTY_PAGE as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests the project's timeline with pagination", async () => {
    await getTeamActivityTimeline(PROJECT_ID, 2, 5);

    expect(api.get).toHaveBeenCalledWith(
      `/projects/${PROJECT_ID}/activity-timeline?page=2&limit=5`,
    );
  });

  it("appends the activity type filter when given one", async () => {
    await getTeamActivityTimeline(PROJECT_ID, 1, 10, "member_joined");

    expect(api.get).toHaveBeenCalledWith(expect.stringContaining("&activity_type=member_joined"));
  });

  it("omits the filter entirely when not given one", async () => {
    await getTeamActivityTimeline(PROJECT_ID);

    expect(api.get).toHaveBeenCalledWith(expect.not.stringContaining("activity_type"));
  });

  it("encodes the filter so a value with a space cannot break the query string", async () => {
    await getTeamActivityTimeline(PROJECT_ID, 1, 10, "role updated&page=99");

    const url = vi.mocked(api.get).mock.calls[0][0] as string;
    expect(url).toContain("activity_type=role%20updated%26page%3D99");
    expect(url).toContain("page=1");
  });

  // The regression. Any failure used to return five invented activities
  // attributed to people who do not exist, with timestamps derived from
  // Date.now() so they always looked recent.
  it("propagates a failure instead of inventing a timeline", async () => {
    vi.spyOn(api, "get").mockRejectedValue(new Error("Network error"));

    await expect(getTeamActivityTimeline(PROJECT_ID)).rejects.toThrow("Network error");
  });

  it("returns an empty timeline as empty", async () => {
    const result = await getTeamActivityTimeline(PROJECT_ID);

    expect(result.items).toEqual([]);
    expect(result.has_more).toBe(false);
  });

  it("returns the real items when there are some", async () => {
    vi.spyOn(api, "get").mockResolvedValue({
      ...EMPTY_PAGE,
      items: [
        {
          id: "real-1",
          project_id: PROJECT_ID,
          activity_type: "member_joined",
          title: "Priya joined the team",
          actor_name: "Priya Raman",
          created_at: "2026-08-20T09:00:00Z",
        },
      ],
      total: 1,
    } as never);

    const result = await getTeamActivityTimeline(PROJECT_ID);

    expect(result.items.map((i) => i.actor_name)).toEqual(["Priya Raman"]);
    // The invented cast from the old fallback.
    expect(result.items.map((i) => i.actor_name)).not.toContain("Sarah Connor");
  });
});
