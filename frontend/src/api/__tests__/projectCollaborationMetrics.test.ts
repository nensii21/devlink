import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getProjectCollaborationMetrics } from "../modules/projectCollaborationMetrics";
import { api } from "../client";

const PROJECT_ID = 42;

const REAL_RESPONSE = {
  project_id: PROJECT_ID,
  active_members: 2,
  total_team_size: 3,
  avg_response_time_hours: 9.5,
  messages_exchanged: 4,
  tasks_completed: 1,
  applications_received: 0,
  collaboration_score: 31,
  daily_activity: [],
};

describe("getProjectCollaborationMetrics", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue(REAL_RESPONSE as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("targets the project-scoped metrics endpoint", async () => {
    await getProjectCollaborationMetrics(PROJECT_ID);

    expect(api.get).toHaveBeenCalledWith(`/projects/${PROJECT_ID}/collaboration-metrics`);
  });

  it("returns what the backend sent", async () => {
    await expect(getProjectCollaborationMetrics(PROJECT_ID)).resolves.toEqual(REAL_RESPONSE);
  });

  // The regression. This used to catch everything and return a fixed object,
  // so a 401, a 500 or an unreachable backend all rendered as a healthy
  // project with a collaboration score of 92.
  it("propagates a failure instead of inventing metrics", async () => {
    vi.spyOn(api, "get").mockRejectedValue(new Error("Request failed with status 500"));

    await expect(getProjectCollaborationMetrics(PROJECT_ID)).rejects.toThrow(
      "Request failed with status 500",
    );
  });

  it("does not substitute a fallback for an unauthorised response", async () => {
    vi.spyOn(api, "get").mockRejectedValue(new Error("401"));

    await expect(getProjectCollaborationMetrics(PROJECT_ID)).rejects.toThrow();
  });

  // A real project can legitimately have a score of zero, or no team, or no
  // messages. The old guard was `if (res && res.project_id)`, which fell
  // through to the mock for anything falsy -- so "quiet project" and "backend
  // is down" produced the same very busy screen.
  it("returns a genuinely empty project as empty", async () => {
    const empty = {
      ...REAL_RESPONSE,
      active_members: 0,
      total_team_size: 0,
      messages_exchanged: 0,
      tasks_completed: 0,
      collaboration_score: 0,
      daily_activity: [],
    };
    vi.spyOn(api, "get").mockResolvedValue(empty as never);

    const result = await getProjectCollaborationMetrics(PROJECT_ID);

    expect(result.collaboration_score).toBe(0);
    expect(result.daily_activity).toEqual([]);
  });

  it("never returns the numbers the old fallback used", async () => {
    const result = await getProjectCollaborationMetrics(PROJECT_ID);

    // 92/342/2.4 were the hardcoded values. Named explicitly so that
    // reintroducing the fallback fails here rather than looking plausible.
    expect(result.collaboration_score).not.toBe(92);
    expect(result.messages_exchanged).not.toBe(342);
    expect(result.avg_response_time_hours).not.toBe(2.4);
  });
});
