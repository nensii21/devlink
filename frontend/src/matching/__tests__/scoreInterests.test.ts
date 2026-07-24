import { describe, it, expect } from "vitest";
import { scoreInterests } from "@/matching/scoreInterests";

describe("scoreInterests", () => {
  it("returns high score for full overlap", () => {
    const result = scoreInterests(["AI", "Web Dev"], ["AI", "Web Dev"]);
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(2);
  });

  it("returns partial score for partial overlap", () => {
    const result = scoreInterests(["AI", "Web Dev"], ["AI", "Healthcare"]);
    expect(result.score).toBeGreaterThan(0);
    expect(result.score).toBeLessThan(100);
    expect(result.matchedCount).toBe(1);
  });

  it("returns zero for no overlap", () => {
    const result = scoreInterests(["AI"], ["Blockchain"]);
    expect(result.score).toBe(0);
    expect(result.matchedCount).toBe(0);
  });

  it("handles case-insensitive matching", () => {
    const result = scoreInterests(["ai", "web dev"], ["AI", "Web Dev"]);
    expect(result.matchedCount).toBe(2);
  });

  it("handles empty developer interests", () => {
    const result = scoreInterests([], ["AI"]);
    expect(result.score).toBe(0);
    expect(result.reason).toContain("No developer interests");
  });

  it("handles empty project tags", () => {
    const result = scoreInterests(["AI"], []);
    expect(result.score).toBe(0);
    expect(result.reason).toContain("No project tags");
  });

  it("handles both empty", () => {
    const result = scoreInterests([], []);
    expect(result.score).toBe(0);
    expect(result.reason).toContain("No interests or tags");
  });

  it("normalizes whitespace", () => {
    const result = scoreInterests(["  AI  "], ["AI"]);
    expect(result.matchedCount).toBe(1);
  });

  it("removes duplicate interests", () => {
    const result = scoreInterests(["AI", "ai", "AI"], ["AI"]);
    expect(result.matchedCount).toBe(1);
  });

  it("returns perfect alignment reason", () => {
    const result = scoreInterests(["AI", "ML"], ["AI", "ML"]);
    expect(result.reason).toContain("Perfect interest alignment");
  });

  it("returns no overlap reason", () => {
    const result = scoreInterests(["AI"], ["Blockchain"]);
    expect(result.reason).toContain("No overlapping interests");
  });
});
