import { describe, it, expect } from "vitest";
import { scoreExperience } from "@/matching/scoreExperience";

describe("scoreExperience", () => {
  it("returns full score when meeting requirement", () => {
    const result = scoreExperience(3, 3);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("Meets");
  });

  it("returns full score when exceeding requirement", () => {
    const result = scoreExperience(5, 3);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("Exceeds");
  });

  it("returns partial score when slightly below", () => {
    const result = scoreExperience(4, 5);
    expect(result.score).toBeGreaterThan(50);
    expect(result.score).toBeLessThan(100);
    expect(result.reason).toContain("Slightly below");
  });

  it("returns low score when far below", () => {
    const result = scoreExperience(1, 5);
    expect(result.score).toBeLessThan(50);
    expect(result.reason).toContain("Significantly below");
  });

  it("returns full score when no requirement specified", () => {
    const result = scoreExperience(2, 0);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("No experience requirement");
  });

  it("handles zero developer experience", () => {
    const result = scoreExperience(0, 3);
    expect(result.score).toBe(0);
    expect(result.reason).toContain("Significantly below");
  });

  it("handles both zero", () => {
    const result = scoreExperience(0, 0);
    expect(result.score).toBe(100);
  });

  it("exceeds by many years", () => {
    const result = scoreExperience(10, 2);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("Exceeds requirement by 8 years");
  });

  it("exceeds by one year uses singular", () => {
    const result = scoreExperience(4, 3);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("Exceeds requirement by 1 year");
  });

  it("clamps negative input gracefully", () => {
    const result = scoreExperience(-1, 3);
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(100);
  });
});
