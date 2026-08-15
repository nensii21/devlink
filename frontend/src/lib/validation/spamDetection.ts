/**
 * Heuristic spam scoring for user-submitted text.
 *
 * This is a hard gate: `postsApi.create` and `postsApi.comment` both throw
 * before the request is sent, so a false positive does not warn anybody, it
 * stops them posting. Two consequences shape everything below.
 *
 * **Match on normalised text, not raw text.** Every check used to run against
 * the raw string, so `fr33 m0n3y`, `b u y  n o w`, `ＢＵＹ ＮＯＷ` and
 * `t․me/foo` (with a one-dot leader instead of a full stop) all scored zero.
 * Normalising first — Unicode folding, homoglyph mapping, invisible-character
 * stripping, leetspeak decoding, spaced-out-letter collapsing — costs one pass
 * and closes all of them at once.
 *
 * **Be reluctant to fire on a developer network.** Posts here are full of
 * stack traces, SQL, `SCREAMING_CONSTANTS`, config blocks and long numeric
 * ids. Code spans are removed before the shape-based checks run, the
 * phone-number check wants something that actually looks like a phone number
 * rather than any ten digits in a row, and every signal is capped so no single
 * one can carry a post over the line on its own.
 */

export interface SpamSignal {
  /** Stable identifier, useful for tuning without parsing prose. */
  id: string;
  /** Human-readable explanation, shown to the person who was blocked. */
  reason: string;
  /** This signal's contribution to the final score, after capping. */
  weight: number;
}

export interface SpamCheckResult {
  isSpam: boolean;
  score: number; // 0 to 1 (higher = more likely spam)
  reasons: string[];
  /** What the checks actually ran against, for debugging a disputed block. */
  normalizedText: string;
  /** Per-signal breakdown, so a reviewer can see which rule fired. */
  signals: SpamSignal[];
}

/** A post scoring at or above this is refused. */
export const SPAM_THRESHOLD = 0.5;

const SPAM_KEYWORDS = [
  "buy now",
  "free money",
  "earn fast",
  "crypto giveaway",
  "telegram group",
  "whatsapp group",
  "click here",
  "cheap price",
  "guaranteed profit",
  "discount code",
  "casino",
  "betting",
  "unlimited followers",
  "dm for info",
  "work from home",
];

/**
 * Link shorteners and chat-invite hosts.
 *
 * Matched as hosts rather than as raw substrings, so a link to an article
 * whose path happens to contain "t.me" is not a hit.
 */
const SUSPICIOUS_HOSTS = [
  "bit.ly",
  "tinyurl.com",
  "t.me",
  "wa.me",
  "is.gd",
  "cutt.ly",
  "rb.gy",
  "shorturl.at",
  "rebrand.ly",
  "discord.gg",
  "buff.ly",
  "ow.ly",
  "shorte.st",
  "adf.ly",
];

/**
 * Characters that render like ASCII punctuation or letters but are not.
 *
 * These are the cheap way past any pattern written in ASCII: `t․me` with a
 * U+2024 one-dot leader looks identical to `t.me` in every font we ship.
 */
const HOMOGLYPHS: Record<string, string> = {
  "․": ".", // one dot leader
  "。": ".", // ideographic full stop
  "．": ".", // fullwidth full stop
  "⁄": "/", // fraction slash
  "∕": "/", // division slash
  "／": "/", // fullwidth solidus
  "：": ":", // fullwidth colon
  а: "a", // cyrillic a
  е: "e", // cyrillic ie
  о: "o", // cyrillic o
  р: "p", // cyrillic er
  с: "c", // cyrillic es
  х: "x", // cyrillic ha
  у: "y", // cyrillic u
  і: "i", // cyrillic byelorussian-ukrainian i
  ο: "o", // greek omicron
  ѕ: "s", // cyrillic dze
};

/**
 * Digits and symbols commonly substituted for letters.
 *
 * `!` is deliberately absent even though `!` for `i` is a real substitution.
 * It is punctuation far more often than it is a letter, and decoding it turns
 * every `free money!` into `free moneyi`, which then matches nothing — a
 * false-negative generator worth more than the handful of `cl!ck` it catches.
 */
const LEET: Record<string, string> = {
  "0": "o",
  "1": "i",
  "3": "e",
  "4": "a",
  "5": "s",
  "7": "t",
  "@": "a",
  $: "s",
};

/** Symbols in `LEET` that are also ordinary punctuation at a word's edge. */
const EDGE_SENSITIVE = new Set(["@", "$"]);

// Zero-width and other invisible characters used to break up a word without
// changing how it looks. Written as escapes on purpose -- as literals they are
// invisible in the source too, which is not something to leave in a regex.
// Soft hyphen, ZWSP/ZWNJ/ZWJ, bidi marks, word joiner, isolates, BOM.
const INVISIBLE = /[\u00AD\u200B-\u200F\u2060\u2066-\u2069\uFEFF]/g;

const URL_PATTERN = /https?:\/\/[^\s<>"')]+/gi;

// Fenced blocks, indented blocks and inline spans. Removed before the checks
// that reason about the *shape* of the text rather than its content.
const FENCED_CODE = /```[\s\S]*?```|~~~[\s\S]*?~~~/g;
const INLINE_CODE = /`[^`\n]+`/g;
const INDENTED_CODE = /^(?: {4}|\t).*$/gm;

/**
 * Something that looks like a phone number, rather than any run of digits.
 *
 * The old pattern was `/\+?[0-9]{10,12}/`, which is every Unix timestamp, id,
 * checksum and large numeric literal anybody has ever pasted into a bug
 * report. A real phone number in a spam post is almost always either written
 * with a country code or grouped with separators, so that is what we ask for.
 */
const PHONE_WITH_COUNTRY_CODE = /(?<![\d+])\+\d[\d\s().-]{7,17}\d(?![\d])/g;
const PHONE_GROUPED = /(?<![\d.-])(?:\(\d{2,4}\)|\d{2,4})[\s.-]\d{2,4}[\s.-]\d{2,5}(?![\d])/g;

/** Per-signal ceilings, so no single rule can carry a post over the line. */
const CAPS = {
  keywords: 0.6,
  hosts: 0.5,
  phone: 0.3,
  links: 0.3,
  shouting: 0.2,
  repeatedChars: 0.2,
  repeatedWords: 0.25,
} as const;

/**
 * Fold a string down to something the patterns can be written against in
 * plain ASCII.
 *
 * Order matters: decompose and strip combining marks first (so `b̷u̷y̷` loses
 * its strikethrough), then recompose under NFKC (so fullwidth and
 * mathematical alphanumerics become ASCII), then map the homoglyphs that
 * Unicode does not consider equivalent.
 */
export function normalizeForMatching(text: string): string {
  const withoutMarks = text.normalize("NFKD").replace(/\p{M}/gu, "").normalize("NFKC");

  const mapped = Array.from(withoutMarks)
    .map((char) => HOMOGLYPHS[char] ?? char)
    .join("");

  return mapped.replace(INVISIBLE, "").toLowerCase();
}

/**
 * Undo leetspeak, but only inside tokens that already contain a letter.
 *
 * `fr33` becomes `free`; `1754985600` is left exactly as it is. Decoding
 * pure-numeric tokens would turn timestamps into nonsense words and is how a
 * naive substitution pass invents matches that were never there.
 */
export function decodeLeetspeak(text: string): string {
  return text.replace(/[\p{L}\p{N}@$]+/gu, (token) => {
    if (!/\p{L}/u.test(token)) return token;
    if (!/[0-9@$]/.test(token)) return token;

    const chars = Array.from(token);
    return chars
      .map((char, index) => {
        // A trailing `$` is a price, not an `s`; a leading `@` is a mention.
        if (EDGE_SENSITIVE.has(char) && (index === 0 || index === chars.length - 1)) {
          return char;
        }
        return LEET[char] ?? char;
      })
      .join("");
  });
}

/**
 * Close up words that were split one character at a time.
 *
 * `b u y  n o w` becomes `buy now`. Two details matter:
 *
 * * only runs of three or more single characters are collapsed, so ordinary
 *   prose (`a b test`, `I am 5 ft`) is left alone
 * * the separator is a *single* space, so the wider gap between the two
 *   spelled-out words still reads as a word break and does not get swallowed
 *
 * Runs of whitespace are then collapsed to one, so the result is comparable
 * against a keyword list written with single spaces.
 */
export function collapseSpacedLetters(text: string): string {
  return text
    .replace(/(?<![\p{L}\p{N}])(?:[\p{L}\p{N}][ \t]){2,}[\p{L}\p{N}](?![\p{L}\p{N}])/gu, (run) =>
      run.replace(/[ \t]/g, ""),
    )
    .replace(/[ \t]{2,}/g, " ");
}

/** Everything that is not prose, removed, for the shape-based checks. */
export function stripCode(text: string): string {
  return text
    .replace(FENCED_CODE, " ")
    .replace(INDENTED_CODE, " ")
    .replace(INLINE_CODE, " ")
    .replace(URL_PATTERN, " ");
}

/**
 * Whether a stretch of text reads more like code than like shouting.
 *
 * A snippet of `MAX_RETRIES`, `SELECT ... FROM`, or a Java stack trace is
 * mostly capitals and mostly repeated tokens, which is exactly what the
 * shouting and repetition rules look for.
 */
function looksLikeCode(text: string): boolean {
  const codeish = /[_{}();]|::|=>|\/\*|\$\{|<\/?\w+>/;
  return codeish.test(text);
}

function hostOf(url: string): string | null {
  try {
    return new URL(url).hostname.toLowerCase().replace(/^www\./, "");
  } catch {
    return null;
  }
}

/** Whether `host` is, or is a subdomain of, `suspect`. */
function hostMatches(host: string, suspect: string): boolean {
  return host === suspect || host.endsWith(`.${suspect}`);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Analyse text for spam markers.
 *
 * Returns a score in `[0, 1]`; `isSpam` is `score >= SPAM_THRESHOLD`.
 */
export function analyzeSpam(text: string): SpamCheckResult {
  const empty: SpamCheckResult = {
    isSpam: false,
    score: 0,
    reasons: [],
    normalizedText: "",
    signals: [],
  };

  if (!text || text.trim().length === 0) return empty;

  const normalized = normalizeForMatching(text);
  const matchable = collapseSpacedLetters(decodeLeetspeak(normalized));

  // Shape-based checks run against prose only. Code and URLs skew both the
  // capitalisation ratio and the token-repetition ratio, and this is a
  // developer network — posts are full of both.
  const prose = stripCode(matchable).trim();
  const proseWords = prose.split(/\s+/).filter(Boolean);

  // The capitalisation check is the one thing that cannot use `matchable`,
  // since normalising lowercases everything. It gets the original text with
  // code and links removed.
  const casedProse = stripCode(text).trim();

  const signals: SpamSignal[] = [];

  const add = (id: string, reason: string, weight: number) => {
    if (weight > 0) signals.push({ id, reason, weight });
  };

  // 1. Keyword phrases, on word boundaries so "casino" does not fire inside a
  //    longer word.
  const matchedKeywords = SPAM_KEYWORDS.filter((keyword) =>
    new RegExp(`(?<![\\p{L}\\p{N}])${escapeRegExp(keyword)}(?![\\p{L}\\p{N}])`, "u").test(
      matchable,
    ),
  );
  if (matchedKeywords.length > 0) {
    add(
      "keywords",
      `Contains potential spam phrasing: "${matchedKeywords.join('", "')}"`,
      Math.min(matchedKeywords.length * 0.3, CAPS.keywords),
    );
  }

  // 2. Link shorteners and chat-invite hosts, matched as hosts.
  const urls = matchable.match(URL_PATTERN) ?? [];
  const hosts = urls.map(hostOf).filter((h): h is string => h !== null);
  const flaggedHosts = [
    ...new Set(
      hosts.filter((host) => SUSPICIOUS_HOSTS.some((suspect) => hostMatches(host, suspect))),
    ),
  ];
  if (flaggedHosts.length > 0) {
    add(
      "suspicious-hosts",
      `Links to a shortener or chat invite: ${flaggedHosts.join(", ")}`,
      Math.min(flaggedHosts.length * 0.35, CAPS.hosts),
    );
  }

  // 3. Contact numbers. Only things shaped like phone numbers count; a bare
  //    run of digits is an id, not a number to call.
  const phoneMatches = [
    ...(normalized.match(PHONE_WITH_COUNTRY_CODE) ?? []),
    ...(normalized.match(PHONE_GROUPED) ?? []),
  ];
  if (phoneMatches.length > 0) {
    add("phone-number", "Contains what looks like a contact phone number", CAPS.phone);
  }

  // 4. Link density, as a ratio rather than an absolute count — a well-sourced
  //    long write-up should not be penalised for having references.
  if (urls.length > 3) {
    const wordsPerLink = proseWords.length / urls.length;
    if (wordsPerLink < 25) {
      add(
        "link-density",
        "Mostly links with very little text around them",
        Math.min(0.15 + (urls.length - 3) * 0.05, CAPS.links),
      );
    }
  }

  // 5. Shouting. Skipped for anything that reads like code, where a high
  //    capital ratio is just constant names.
  if (casedProse.length > 40 && !looksLikeCode(casedProse)) {
    const letters = casedProse.match(/\p{L}/gu) ?? [];
    const capitals = casedProse.match(/\p{Lu}/gu) ?? [];
    if (letters.length > 0 && capitals.length / letters.length > 0.6) {
      add("shouting", "Excessive use of capital letters", CAPS.shouting);
    }
  }

  // 6. Runs of a single repeated character ("looooook at thiiiiis").
  if (/(.)\1{5,}/.test(prose)) {
    add("repeated-characters", "Repeated character patterns detected", CAPS.repeatedChars);
  }

  // 7. Token repetition, again skipped for code, and needing enough words to
  //    be meaningful.
  if (proseWords.length > 12 && !looksLikeCode(prose)) {
    const unique = new Set(proseWords);
    if (unique.size / proseWords.length < 0.4) {
      add("repeated-words", "High degree of repetitive words", CAPS.repeatedWords);
    }
  }

  const score = Math.min(
    signals.reduce((total, signal) => total + signal.weight, 0),
    1,
  );

  return {
    isSpam: score >= SPAM_THRESHOLD,
    score,
    reasons: signals.map((signal) => signal.reason),
    normalizedText: matchable,
    signals,
  };
}
