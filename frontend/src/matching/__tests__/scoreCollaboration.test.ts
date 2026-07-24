import { describe, it, expect } from "vitest";
import { scoreCollaboration } from "@/matching/scoreCollaboration";
import type { CollaborationHistory } from "@/matching/types";

const emptyHistory: CollaborationHistory = {
  previousOwnerIds: [],
  previousMaintainerIds: [],
  previousOrgIds: [],
  previousContributorIds: [],
};

describe("scoreCollaboration", () => {
  it("returns high score for previous owner collaboration", () => {
    const history: CollaborationHistory = {
      ...emptyHistory,
      previousOwnerIds: ["owner-1"],
    };
    const result = scoreCollaboration("dev-1", history, "owner-1", [], null, []);
    expect(result.score).toBe(80);
    expect(result.hasPreviousCollaboration).toBe(true);
    expect(result.collaborationType).toBe("project owner");
  });

  it("returns score for maintainer collaboration", () => {
    const history: CollaborationHistory = {
      ...emptyHistory,
      previousMaintainerIds: ["maintainer-1"],
    };
    const result = scoreCollaboration("dev-1", history, "owner-other", ["maintainer-1"], null, []);
    expect(result.score).toBe(60);
    expect(result.hasPreviousCollaboration).toBe(true);
    expect(result.collaborationType).toBe("project maintainer");
  });

  it("returns score for org collaboration", () => {
    const history: CollaborationHistory = {
      ...emptyHistory,
      previousOrgIds: ["org-1"],
    };
    const result = scoreCollaboration("dev-1", history, "owner-other", [], "org-1", []);
    expect(result.score).toBe(40);
    expect(result.hasPreviousCollaboration).toBe(true);
    expect(result.collaborationType).toBe("organization");
  });

  it("returns score for contributor collaboration", () => {
    const history: CollaborationHistory = {
      ...emptyHistory,
      previousContributorIds: ["contributor-1"],
    };
    const result = scoreCollaboration("dev-1", history, "owner-other", [], null, ["contributor-1"]);
    expect(result.score).toBe(30);
    expect(result.hasPreviousCollaboration).toBe(true);
    expect(result.collaborationType).toBe("contributor");
  });

  it("returns zero for no collaboration", () => {
    const result = scoreCollaboration("dev-1", emptyHistory, "owner-1", ["maintainer-1"], "org-1", [
      "contributor-1",
    ]);
    expect(result.score).toBe(0);
    expect(result.hasPreviousCollaboration).toBe(false);
    expect(result.reason).toContain("No previous collaboration");
  });

  it("prioritizes owner over other types", () => {
    const history: CollaborationHistory = {
      previousOwnerIds: ["owner-1"],
      previousMaintainerIds: ["maintainer-1"],
      previousOrgIds: ["org-1"],
      previousContributorIds: ["contributor-1"],
    };
    const result = scoreCollaboration("dev-1", history, "owner-1", ["maintainer-1"], "org-1", [
      "contributor-1",
    ]);
    expect(result.collaborationType).toBe("project owner");
  });
});
