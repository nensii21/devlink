import { describe, it, expect } from "vitest";
import { scoreAvailability } from "@/matching/scoreAvailability";

describe("scoreAvailability", () => {
  it("returns full score for exact match", () => {
    const result = scoreAvailability(20, 20);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("meets");
  });

  it("returns full score when exceeding requirement", () => {
    const result = scoreAvailability(30, 20);
    expect(result.score).toBeGreaterThanOrEqual(80);
    expect(result.reason).toContain("meets or exceeds");
  });

  it("returns partial score for slight mismatch", () => {
    const result = scoreAvailability(18, 20);
    expect(result.score).toBeGreaterThan(50);
    expect(result.score).toBeLessThan(100);
  });

  it("returns lower score for large mismatch", () => {
    const result = scoreAvailability(5, 20);
    expect(result.score).toBeLessThan(50);
    expect(result.reason).toContain("below");
  });

  it("returns full score when no requirement", () => {
    const result = scoreAvailability(20, 0);
    expect(result.score).toBe(100);
    expect(result.reason).toContain("No availability requirement");
  });

  it("handles zero developer availability", () => {
    const result = scoreAvailability(0, 20);
    expect(result.score).toBe(0);
  });

  it("handles both zero", () => {
    const result = scoreAvailability(0, 0);
    expect(result.score).toBe(100);
  });

  it("handles moderate mismatch", () => {
    const result = scoreAvailability(10, 20);
    expect(result.score).toBeGreaterThan(0);
    expect(result.score).toBeLessThan(100);
    expect(result.reason).toContain("below");
  });

  it("clamps negative input", () => {
    const result = scoreAvailability(-5, 20);
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(100);
  });
});
