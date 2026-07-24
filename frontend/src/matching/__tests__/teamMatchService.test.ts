import { describe, it, expect } from "vitest";
import { teamMatchService } from "@/services/teamMatch";
import { builders, projects } from "@/mocks/seed";

describe("teamMatchService", () => {
  describe("calculateForBuilder", () => {
    it("returns a valid MatchResult", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result).toHaveProperty("totalScore");
      expect(result).toHaveProperty("breakdown");
      expect(result).toHaveProperty("summary");
      expect(result.totalScore).toBeGreaterThanOrEqual(0);
      expect(result.totalScore).toBeLessThanOrEqual(100);
    });

    it("includes all five breakdown categories", () => {
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      expect(result.breakdown).toHaveProperty("skills");
      expect(result.breakdown).toHaveProperty("experience");
      expect(result.breakdown).toHaveProperty("interests");
      expect(result.breakdown).toHaveProperty("availability");
      expect(result.breakdown).toHaveProperty("collaboration");
    });

    it("accepts custom weights", () => {
      const weights = {
        skills: 1.0,
        experience: 0,
        interests: 0,
        availability: 0,
        collaboration: 0,
      };
      const result = teamMatchService.calculateForBuilder(builders[0], projects[0], weights);
      expect(result.breakdown.experience).toBe(0);
      expect(result.breakdown.interests).toBe(0);
      expect(result.breakdown.availability).toBe(0);
      expect(result.breakdown.collaboration).toBe(0);
    });

    it("produces different scores for different builders", () => {
      const result1 = teamMatchService.calculateForBuilder(builders[0], projects[0]);
      const result2 = teamMatchService.calculateForBuilder(builders[2], projects[0]);
      expect(result1.totalScore).not.toBe(result2.totalScore);
    });
  });

  describe("rankBuildersForProject", () => {
    it("returns builders sorted by score descending", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      expect(rankings.length).toBeGreaterThan(0);
      for (let i = 1; i < rankings.length; i++) {
        expect(rankings[i - 1].match.totalScore).toBeGreaterThanOrEqual(
          rankings[i].match.totalScore,
        );
      }
    });

    it("includes builder reference in each ranking", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      rankings.forEach(({ builder, match }) => {
        expect(builder).toHaveProperty("id");
        expect(builder).toHaveProperty("name");
        expect(match).toHaveProperty("totalScore");
      });
    });

    it("returns all seed builders", () => {
      const rankings = teamMatchService.rankBuildersForProject(projects[0]);
      expect(rankings.length).toBe(builders.length);
    });
  });

  describe("calculate", () => {
    it("returns a valid MatchResult for known ids", async () => {
      const result = await teamMatchService.calculate("b1", "p1");
      expect(result.totalScore).toBeGreaterThanOrEqual(0);
      expect(result.totalScore).toBeLessThanOrEqual(100);
      expect(result.breakdown).toBeDefined();
      expect(result.summary.length).toBeGreaterThan(0);
    });

    it("returns zero score for unknown developer", async () => {
      const result = await teamMatchService.calculate("unknown", "p1");
      expect(result.totalScore).toBe(0);
      expect(result.summary).toContain("Developer or project not found.");
    });

    it("returns zero score for unknown project", async () => {
      const result = await teamMatchService.calculate("b1", "unknown");
      expect(result.totalScore).toBe(0);
    });

    it("accepts custom weights", async () => {
      const weights = {
        skills: 1.0,
        experience: 0,
        interests: 0,
        availability: 0,
        collaboration: 0,
      };
      const result = await teamMatchService.calculate("b1", "p1", weights);
      expect(result.breakdown.experience).toBe(0);
    });
  });
});
