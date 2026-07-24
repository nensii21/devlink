import type { MatchWeights } from "./types";

export const DEFAULT_MATCH_WEIGHTS: MatchWeights = {
  skills: 0.4,
  experience: 0.2,
  interests: 0.15,
  availability: 0.15,
  collaboration: 0.1,
};

export const SCORE_BOUNDS = {
  min: 0,
  max: 100,
} as const;

export const EXPERIENCE_THRESHOLDS = {
  exceedsBonus: 0,
  meetsScore: 1.0,
  slightlyBelowThreshold: 0.8,
  slightlyBelowScore: 0.6,
  farBelowScore: 0.2,
} as const;

export const COLLABORATION_BONUS = {
  ownerBonus: 0.8,
  maintainerBonus: 0.6,
  orgBonus: 0.4,
  contributorBonus: 0.3,
  maxBonus: 1.0,
} as const;

export const STOPWORDS: ReadonlySet<string> = new Set([
  "the",
  "a",
  "an",
  "and",
  "or",
  "of",
  "to",
  "in",
  "on",
  "for",
  "with",
  "is",
  "are",
  "be",
  "by",
  "at",
  "as",
  "it",
  "this",
  "that",
  "from",
  "we",
  "our",
  "you",
  "your",
  "i",
  "my",
  "me",
  "us",
  "them",
  "they",
  "he",
  "she",
  "his",
  "her",
  "who",
  "what",
  "where",
  "when",
  "how",
]);

export const MIN_TOKEN_LENGTH = 3;
