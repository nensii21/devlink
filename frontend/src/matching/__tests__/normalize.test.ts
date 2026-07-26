import { describe, it, expect } from "vitest";
import {
  normalizeString,
  normalizeSkill,
  normalizeSkills,
  tokenize,
  computeJaccardIndex,
  computeOverlapRatio,
  clamp,
  toScore,
} from "@/matching/normalize";

describe("normalizeString", () => {
  it("lowercases input", () => {
    expect(normalizeString("Hello World")).toBe("hello world");
  });

  it("trims whitespace", () => {
    expect(normalizeString("  hello  ")).toBe("hello");
  });

  it("normalizes multiple spaces", () => {
    expect(normalizeString("hello   world")).toBe("hello world");
  });
});

describe("normalizeSkill", () => {
  it("normalizes a skill name", () => {
    expect(normalizeSkill("  React  ")).toBe("react");
  });

  it("handles mixed case", () => {
    expect(normalizeSkill("TypeScript")).toBe("typescript");
  });
});

describe("normalizeSkills", () => {
  it("removes duplicates", () => {
    const result = normalizeSkills(["React", "react", "REACT"]);
    expect(result).toEqual(["react"]);
  });

  it("normalizes all skills", () => {
    const result = normalizeSkills(["  React  ", " TypeScript "]);
    expect(result).toEqual(["react", "typescript"]);
  });
});

describe("tokenize", () => {
  it("tokenizes text into lowercase tokens", () => {
    const tokens = tokenize("Hello World");
    expect(tokens).toEqual(new Set(["hello", "world"]));
  });

  it("removes stopwords", () => {
    const tokens = tokenize("the quick brown fox");
    expect(tokens).toEqual(new Set(["quick", "brown", "fox"]));
  });

  it("removes short tokens", () => {
    const tokens = tokenize("a bb ccc");
    expect(tokens).toEqual(new Set(["ccc"]));
  });

  it("handles empty string", () => {
    const tokens = tokenize("");
    expect(tokens.size).toBe(0);
  });

  it("removes special characters", () => {
    const tokens = tokenize("hello-world!");
    expect(tokens).toEqual(new Set(["helloworld"]));
  });
});

describe("computeJaccardIndex", () => {
  it("returns 1 for identical sets", () => {
    const result = computeJaccardIndex(new Set(["a", "b"]), new Set(["a", "b"]));
    expect(result).toBe(1);
  });

  it("returns 0 for disjoint sets", () => {
    const result = computeJaccardIndex(new Set(["a"]), new Set(["b"]));
    expect(result).toBe(0);
  });

  it("computes correct Jaccard index", () => {
    const result = computeJaccardIndex(new Set(["a", "b", "c"]), new Set(["b", "c", "d"]));
    expect(result).toBe(0.5);
  });

  it("returns 0 for both empty sets", () => {
    const result = computeJaccardIndex(new Set(), new Set());
    expect(result).toBe(0);
  });
});

describe("computeOverlapRatio", () => {
  it("returns 1 when all items in subset are in superset", () => {
    const result = computeOverlapRatio(new Set(["a", "b"]), new Set(["a", "b", "c"]));
    expect(result).toBe(1);
  });

  it("returns 0 when no overlap", () => {
    const result = computeOverlapRatio(new Set(["d"]), new Set(["a", "b", "c"]));
    expect(result).toBe(0);
  });

  it("returns 0 for empty superset", () => {
    const result = computeOverlapRatio(new Set(["a"]), new Set());
    expect(result).toBe(0);
  });

  it("returns 0 for empty subset", () => {
    const result = computeOverlapRatio(new Set(), new Set(["a"]));
    expect(result).toBe(0);
  });
});

describe("clamp", () => {
  it("returns value within range", () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it("clamps to min", () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it("clamps to max", () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });
});

describe("toScore", () => {
  it("converts 1 to 100", () => {
    expect(toScore(1)).toBe(100);
  });

  it("converts 0 to 0", () => {
    expect(toScore(0)).toBe(0);
  });

  it("converts 0.5 to 50", () => {
    expect(toScore(0.5)).toBe(50);
  });

  it("clamps values above 1", () => {
    expect(toScore(1.5)).toBe(100);
  });

  it("clamps values below 0", () => {
    expect(toScore(-0.5)).toBe(0);
  });
});
