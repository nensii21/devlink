import { describe, it, expect } from "vitest";
import {
  calculateMatch,
  WeightedMatchStrategy,
  calculateMatchWithStrategy,
} from "@/matching/calculateMatch";
import type { Developer, ProjectRequirements } from "@/matching/types";
import { DEFAULT_MATCH_WEIGHTS } from "@/matching/constants";

const baseDeveloper: Developer = {
  id: "dev-1",
  name: "Jane Doe",
  handle: "jane",
  role: "Frontend Developer",
  avatar: "",
  country: "US",
  yearsExp: 4,
  skills: ["React", "TypeScript", "Node.js"],
  interests: ["AI", "Web Dev"],
  availabilityHoursPerWeek: 20,
  collaborationHistory: {
    previousOwnerIds: [],
    previousMaintainerIds: [],
    previousOrgIds: [],
    previousContributorIds: [],
  },
  online: true,
  bio: "Frontend dev",
  lastActiveAt: null,
};

const baseProject: ProjectRequirements = {
  id: "proj-1",
  name: "AI Chatbot",
  description: "Multi-agent bot",
  requiredSkills: ["React", "TypeScript"],
  preferredSkills: ["Node.js"],
  tags: ["AI", "Web Dev"],
  requiredExperienceYears: 3,
  requiredAvailabilityHoursPerWeek: 15,
  ownerId: "owner-1",
  maintainerIds: [],
  orgId: null,
  contributorIds: [],
};

describe("calculateMatch", () => {
  it("returns high score for good match", () => {
    const result = calculateMatch(baseDeveloper, baseProject);
    expect(result.totalScore).toBeGreaterThan(70);
    expect(result.totalScore).toBeLessThanOrEqual(100);
    expect(result.breakdown).toBeDefined();
    expect(result.summary.length).toBeGreaterThan(0);
  });

  it("returns score within 0-100 range", () => {
    const result = calculateMatch(baseDeveloper, baseProject);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });

  it("returns lower score for poor match", () => {
    const poorDeveloper: Developer = {
      ...baseDeveloper,
      skills: ["Python", "Django"],
      interests: ["Blockchain"],
      yearsExp: 1,
      availabilityHoursPerWeek: 5,
    };
    const result = calculateMatch(poorDeveloper, baseProject);
    expect(result.totalScore).toBeLessThan(50);
  });

  it("includes all breakdown categories", () => {
    const result = calculateMatch(baseDeveloper, baseProject);
    expect(result.breakdown).toHaveProperty("skills");
    expect(result.breakdown).toHaveProperty("experience");
    expect(result.breakdown).toHaveProperty("interests");
    expect(result.breakdown).toHaveProperty("availability");
    expect(result.breakdown).toHaveProperty("collaboration");
  });

  it("respects custom weights", () => {
    const customWeights = {
      ...DEFAULT_MATCH_WEIGHTS,
      skills: 0.8,
      experience: 0.1,
      interests: 0.05,
      availability: 0.03,
      collaboration: 0.02,
    };
    const result = calculateMatch(baseDeveloper, baseProject, customWeights);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });

  it("awards collaboration bonus", () => {
    const devWithCollab: Developer = {
      ...baseDeveloper,
      collaborationHistory: {
        previousOwnerIds: ["owner-1"],
        previousMaintainerIds: [],
        previousOrgIds: [],
        previousContributorIds: [],
      },
    };
    const resultCollab = calculateMatch(devWithCollab, baseProject);
    const resultNoCollab = calculateMatch(baseDeveloper, baseProject);
    expect(resultCollab.totalScore).toBeGreaterThanOrEqual(resultNoCollab.totalScore);
  });

  it("handles empty skills gracefully", () => {
    const devNoSkills: Developer = { ...baseDeveloper, skills: [] };
    const projNoSkills: ProjectRequirements = {
      ...baseProject,
      requiredSkills: [],
      preferredSkills: [],
    };
    const result = calculateMatch(devNoSkills, projNoSkills);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });

  it("handles empty interests gracefully", () => {
    const devNoInterests: Developer = { ...baseDeveloper, interests: [] };
    const projNoTags: ProjectRequirements = { ...baseProject, tags: [] };
    const result = calculateMatch(devNoInterests, projNoTags);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
  });

  it("handles zero experience requirement", () => {
    const projNoExp: ProjectRequirements = {
      ...baseProject,
      requiredExperienceYears: 0,
    };
    const result = calculateMatch(baseDeveloper, projNoExp);
    expect(result.breakdown.experience).toBe(20);
  });

  it("handles zero availability requirement", () => {
    const projNoAvail: ProjectRequirements = {
      ...baseProject,
      requiredAvailabilityHoursPerWeek: 0,
    };
    const result = calculateMatch(baseDeveloper, projNoAvail);
    expect(result.breakdown.availability).toBe(15);
  });

  it("generates meaningful summary", () => {
    const result = calculateMatch(baseDeveloper, baseProject);
    expect(result.summary.length).toBeGreaterThan(0);
    result.summary.forEach((s) => {
      expect(typeof s).toBe("string");
      expect(s.length).toBeGreaterThan(0);
    });
  });
});

describe("WeightedMatchStrategy", () => {
  it("implements MatchStrategy interface", () => {
    const strategy = new WeightedMatchStrategy();
    const result = strategy.calculate(baseDeveloper, baseProject);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });

  it("accepts custom weights", () => {
    const strategy = new WeightedMatchStrategy({
      skills: 1.0,
      experience: 0,
      interests: 0,
      availability: 0,
      collaboration: 0,
    });
    const result = strategy.calculate(baseDeveloper, baseProject);
    expect(result.breakdown.experience).toBe(0);
    expect(result.breakdown.interests).toBe(0);
    expect(result.breakdown.availability).toBe(0);
    expect(result.breakdown.collaboration).toBe(0);
  });
});

describe("calculateMatchWithStrategy", () => {
  it("uses provided strategy", () => {
    const strategy = new WeightedMatchStrategy();
    const result = calculateMatchWithStrategy(baseDeveloper, baseProject, strategy);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });
});

describe("edge cases", () => {
  it("handles extremely large skill lists", () => {
    const manySkills = Array.from({ length: 100 }, (_, i) => `Skill${i}`);
    const dev: Developer = { ...baseDeveloper, skills: manySkills.slice(0, 50) };
    const proj: ProjectRequirements = { ...baseProject, requiredSkills: manySkills };
    const result = calculateMatch(dev, proj);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
    expect(result.totalScore).toBeLessThanOrEqual(100);
  });

  it("handles negative years gracefully", () => {
    const dev: Developer = { ...baseDeveloper, yearsExp: -1 };
    const result = calculateMatch(dev, baseProject);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
  });

  it("handles negative availability gracefully", () => {
    const dev: Developer = { ...baseDeveloper, availabilityHoursPerWeek: -5 };
    const result = calculateMatch(dev, baseProject);
    expect(result.totalScore).toBeGreaterThanOrEqual(0);
  });

  it("handles empty collaboration history", () => {
    const dev: Developer = {
      ...baseDeveloper,
      collaborationHistory: {
        previousOwnerIds: [],
        previousMaintainerIds: [],
        previousOrgIds: [],
        previousContributorIds: [],
      },
    };
    const result = calculateMatch(dev, baseProject);
    expect(result.breakdown.collaboration).toBe(0);
  });
});
