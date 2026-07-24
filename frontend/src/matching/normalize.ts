import { STOPWORDS, MIN_TOKEN_LENGTH } from "./constants";

export function normalizeString(input: string): string {
  return input.toLowerCase().trim().replace(/\s+/g, " ");
}

export function normalizeSkill(skill: string): string {
  return normalizeString(skill);
}

export function normalizeSkills(skills: string[]): string[] {
  const normalized = new Set(skills.map(normalizeSkill));
  return Array.from(normalized);
}

export function tokenize(text: string): Set<string> {
  const tokens = new Set<string>();
  const words = normalizeString(text).split(/\s+/);

  for (const raw of words) {
    const cleaned = raw.replace(/[^a-z0-9]/g, "");
    if (cleaned.length < MIN_TOKEN_LENGTH) continue;
    if (STOPWORDS.has(cleaned)) continue;
    tokens.add(cleaned);
  }

  return tokens;
}

export function computeJaccardIndex(setA: Set<string>, setB: Set<string>): number {
  if (setA.size === 0 && setB.size === 0) return 0;

  let intersectionSize = 0;
  for (const item of setA) {
    if (setB.has(item)) intersectionSize++;
  }

  const unionSize = setA.size + setB.size - intersectionSize;
  if (unionSize === 0) return 0;

  return intersectionSize / unionSize;
}

export function computeOverlapRatio(subset: Set<string>, superset: Set<string>): number {
  if (superset.size === 0) return 0;
  if (subset.size === 0) return 0;

  let matchCount = 0;
  for (const item of subset) {
    if (superset.has(item)) matchCount++;
  }

  return matchCount / subset.size;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function toScore(value: number): number {
  return Math.round(clamp(value, 0, 1) * 100);
}
