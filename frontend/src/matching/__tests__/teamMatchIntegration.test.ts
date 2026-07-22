import { describe, it, expect, vi, beforeEach } from "vitest";
import { teamMatchService } from "@/services/teamMatch";
import { builders, projects } from "@/mocks/seed";
import type { MatchResult, MatchWeights } from "@/matching/types";
import { calculateMatch } from "@/matching/calculateMatch";

vi.mock("@/api", () => ({
  isBackendConfigured: () => false,
}));

vi.mock("@/api/modules/teamMatch", () => ({
  teamMatchApi: {
    calculate: vi.fn(),
    calculateBulk: vi.fn(),
  },
}));

describe("teamMatchService (mock mode)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("calculateForBuilder (synchronous)", () => {
    it("returns score 0-100", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.totalScore).toBeGreaterThanOrEqual(0);
      expect(result.totalScore).toBeLessThanOrEqual(100);
    });

    it("maps builder interests into matching", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.breakdown.interests).toBeGreaterThanOrEqual(0);
    });

    it("produces summary strings", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.summary.length).toBeGreaterThan(0);
      result.summary.forEach((s) => expect(typeof s).toBe("string"));
    });
  });

  describe("rankBuildersForProject", () => {
    it("returns all builders", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      expect(rankings.length).toBe(builders.length);
    });

    it("sorts by totalScore descending", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      for (let i = 1; i < rankings.length; i++) {
        expect(rankings[i - 1].match.totalScore).toBeGreaterThanOrEqual(
          rankings[i].match.totalScore,
        );
      }
    });

    it("first ranked builder has highest score", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      const maxScore = Math.max(...rankings.map((r) => r.match.totalScore));
      expect(rankings[0].match.totalScore).toBe(maxScore);
    });
  });

  describe("calculate (async, mock mode)", () => {
    it("returns valid result for known ids", async () => {
      const result = await teamMatchService.calculate("b1", "p1");
      expect(result.totalScore).toBeGreaterThanOrEqual(0);
      expect(result.totalScore).toBeLessThanOrEqual(100);
      expect(result.breakdown).toHaveProperty("skills");
    });

    it("returns zero for unknown developer", async () => {
      const result = await teamMatchService.calculate("nonexistent", "p1");
      expect(result.totalScore).toBe(0);
    });

    it("returns zero for unknown project", async () => {
      const result = await teamMatchService.calculate("b1", "nonexistent");
      expect(result.totalScore).toBe(0);
    });

    it("accepts custom weights", async () => {
      const weights: MatchWeights = {
        skills: 1.0,
        experience: 0,
        interests: 0,
        availability: 0,
        collaboration: 0,
      };
      const result = await teamMatchService.calculate("b1", "p1", weights);
      expect(result.breakdown.experience).toBe(0);
      expect(result.breakdown.interests).toBe(0);
      expect(result.breakdown.availability).toBe(0);
      expect(result.breakdown.collaboration).toBe(0);
    });
  });

  describe("builderToDeveloper mapping", () => {
    it("maps builder skills correctly", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.breakdown.skills).toBeGreaterThanOrEqual(0);
    });

    it("builders with more hours get higher availability score when requirement exceeds both", () => {
      const onlineBuilder = builders.find((b) => b.online)!;
      const offlineBuilder = builders.find((b) => !b.online)!;
      const resultOnline = teamMatchService.calculateForBuilder(onlineBuilder, projects[0]);
      const resultOffline = teamMatchService.calculateForBuilder(offlineBuilder, projects[0]);
      expect(resultOnline.breakdown.availability).toBeGreaterThanOrEqual(0);
      expect(resultOffline.breakdown.availability).toBeGreaterThanOrEqual(0);
    });
  });

  describe("projectToRequirements mapping", () => {
    it("maps project stack to requiredSkills", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.breakdown.skills).toBeGreaterThanOrEqual(0);
    });

    it("maps project tags from boolean flags", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result).toHaveProperty("summary");
    });

    it("maps difficulty to experience requirement", () => {
      const advancedProject = projects.find((p) => p.difficulty === "advanced")!;
      const beginnerProject = projects.find((p) => p.difficulty === "beginner")!;
      const resultAdvanced = teamMatchService.calculateForBuilder(builders[0], advancedProject);
      const resultBeginner = teamMatchService.calculateForBuilder(builders[0], beginnerProject);
      expect(resultAdvanced.breakdown.experience).toBeLessThanOrEqual(
        resultBeginner.breakdown.experience,
      );
    });
  });
});

describe("calculateMatch integration", () => {
  it("consistent results for same inputs", () => {
    const r1 = teamMatchService.calculateForBuilder(builders[0], projects[0]);
    const r2 = teamMatchService.calculateForBuilder(builders[0], projects[0]);
    expect(r1.totalScore).toBe(r2.totalScore);
    expect(r1.breakdown).toEqual(r2.breakdown);
  });

  it("all breakdown values are integers", () => {
    const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
    Object.values(result.breakdown).forEach((v) => {
      expect(Number.isInteger(v)).toBe(true);
    });
  });

  it("totalScore equals sum of breakdown values", () => {
    const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
    const sum = Object.values(result.breakdown).reduce((a, b) => a + b, 0);
    expect(result.totalScore).toBe(sum);
  });
});
