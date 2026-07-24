import { describe, it, expect } from "vitest";
import { scoreSkills } from "@/matching/scoreSkills";

describe("scoreSkills", () => {
  it("returns full score for complete required skill match", () => {
    const result = scoreSkills(
      ["React", "TypeScript", "Node.js"],
      ["React", "TypeScript", "Node.js"],
      [],
    );
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(3);
    expect(result.matchedSkills).toEqual(
      expect.arrayContaining(["react", "typescript", "node.js"]),
    );
  });

  it("returns partial score for partial required skill match", () => {
    const result = scoreSkills(
      ["React", "TypeScript", "Node.js"],
      ["React", "TypeScript", "Docker"],
      [],
    );
    expect(result.score).toBe(67);
    expect(result.matchedCount).toBe(2);
  });

  it("returns zero for no matching skills", () => {
    const result = scoreSkills(["Python", "Django"], ["React", "TypeScript"], []);
    expect(result.score).toBe(0);
    expect(result.matchedCount).toBe(0);
    expect(result.matchedSkills).toEqual([]);
  });

  it("handles duplicate skills by normalizing", () => {
    const result = scoreSkills(["React", "react", "REACT"], ["React", "TypeScript"], []);
    expect(result.matchedCount).toBeGreaterThanOrEqual(1);
    expect(result.matchedCount).toBeLessThanOrEqual(3);
  });

  it("performs case-insensitive comparison", () => {
    const result = scoreSkills(["react", "TYPESCRIPT"], ["React", "TypeScript"], []);
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(2);
  });

  it("normalizes whitespace in skills", () => {
    const result = scoreSkills(["  React  ", " TypeScript "], ["React", "TypeScript"], []);
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(2);
  });

  it("includes preferred skills as bonus", () => {
    const result = scoreSkills(
      ["React", "TypeScript", "Docker"],
      ["React", "TypeScript"],
      ["Docker"],
    );
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(3);
  });

  it("returns zero when no skills required and no preferred", () => {
    const result = scoreSkills(["React"], [], []);
    expect(result.score).toBe(0);
    expect(result.reason).toContain("No skills required");
  });

  it("handles empty developer skills", () => {
    const result = scoreSkills([], ["React", "TypeScript"], []);
    expect(result.score).toBe(0);
    expect(result.matchedCount).toBe(0);
  });

  it("handles both empty", () => {
    const result = scoreSkills([], [], []);
    expect(result.score).toBe(0);
  });

  it("handles preferred skills only", () => {
    const result = scoreSkills(["React", "TypeScript"], [], ["React", "TypeScript"]);
    expect(result.score).toBe(100);
    expect(result.matchedCount).toBe(2);
  });

  it("provides correct reason for full required match", () => {
    const result = scoreSkills(["React", "TypeScript"], ["React", "TypeScript"], []);
    expect(result.reason).toContain("all");
  });

  it("provides correct reason for partial match", () => {
    const result = scoreSkills(["React"], ["React", "TypeScript"], []);
    expect(result.reason).toContain("1 of 2");
  });

  it("provides correct reason for no match", () => {
    const result = scoreSkills(["Python"], ["React", "TypeScript"], []);
    expect(result.reason).toContain("No matching skills");
  });
});
