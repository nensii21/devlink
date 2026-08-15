import { describe, expect, it } from "vitest";

import {
  SPAM_THRESHOLD,
  analyzeSpam,
  collapseSpacedLetters,
  decodeLeetspeak,
  normalizeForMatching,
} from "../spamDetection";

/** `analyzeSpam` gates posting, so "blocked" is the thing worth asserting on. */
function isBlocked(text: string): boolean {
  return analyzeSpam(text).isSpam;
}

function signalIds(text: string): string[] {
  return analyzeSpam(text).signals.map((s) => s.id);
}

describe("normalizeForMatching", () => {
  it("folds fullwidth characters to ASCII", () => {
    expect(normalizeForMatching("ＢＵＹ ＮＯＷ")).toBe("buy now");
  });

  it("folds mathematical alphanumerics to ASCII", () => {
    expect(normalizeForMatching("𝐛𝐮𝐲 𝐧𝐨𝐰")).toBe("buy now");
  });

  it("strips zero-width characters", () => {
    expect(normalizeForMatching("buy​now")).toBe("buynow");
  });

  it("strips soft hyphens", () => {
    expect(normalizeForMatching("buy­now")).toBe("buynow");
  });

  it("strips combining marks", () => {
    expect(normalizeForMatching("b̶u̶y̶")).toBe("buy");
  });

  it("maps a one-dot leader to a full stop", () => {
    expect(normalizeForMatching("t․me")).toBe("t.me");
  });

  it("maps cyrillic lookalikes to latin", () => {
    // Cyrillic es, a and o in place of the latin c, a and o.
    expect(normalizeForMatching("саsinо")).toBe("casino");
  });

  it("leaves ordinary text alone apart from casing", () => {
    expect(normalizeForMatching("Hello World")).toBe("hello world");
  });
});

describe("decodeLeetspeak", () => {
  it("decodes digits inside words", () => {
    expect(decodeLeetspeak("fr33 m0n3y")).toBe("free money");
  });

  it("decodes symbol substitutions", () => {
    expect(decodeLeetspeak("c@sino")).toBe("casino");
  });

  it("leaves a pure number alone", () => {
    // The whole reason to scope this: a timestamp must not become a word.
    expect(decodeLeetspeak("1754985600")).toBe("1754985600");
  });

  it("leaves a word with no substitutions alone", () => {
    expect(decodeLeetspeak("hello world")).toBe("hello world");
  });

  it("does not touch numbers next to words", () => {
    expect(decodeLeetspeak("issue 1234567890 is open")).toContain("1234567890");
  });

  it("leaves a trailing exclamation mark as punctuation", () => {
    // Decoding `!` to `i` turns "free money!" into "free moneyi", which then
    // matches no keyword at all — it loses far more than it catches.
    expect(decodeLeetspeak("free money!")).toBe("free money!");
  });

  it("leaves a trailing dollar sign as a currency symbol", () => {
    expect(decodeLeetspeak("price$")).toBe("price$");
  });

  it("leaves a leading at sign as a mention", () => {
    expect(decodeLeetspeak("@alice")).toBe("@alice");
  });

  it("still decodes a symbol in the middle of a word", () => {
    expect(decodeLeetspeak("ca$ino")).toBe("casino");
  });
});

describe("collapseSpacedLetters", () => {
  it("closes up a spelled-out word", () => {
    expect(collapseSpacedLetters("b u y  n o w")).toBe("buy now");
  });

  it("leaves short sequences alone", () => {
    // Two single letters is ordinary prose, not obfuscation.
    expect(collapseSpacedLetters("a b test")).toBe("a b test");
  });

  it("leaves normal words alone", () => {
    expect(collapseSpacedLetters("this is a normal sentence")).toBe("this is a normal sentence");
  });

  it("treats a wider gap as a word break", () => {
    // Collapsing across the double space would give "buynow", which matches
    // nothing. The gap is what tells the two spelled-out words apart.
    expect(collapseSpacedLetters("b u y  n o w")).not.toBe("buynow");
  });
});

describe("analyzeSpam — legitimate posts are not blocked", () => {
  const legitimate: [string, string][] = [
    [
      "a unix timestamp",
      "Reproduced this at epoch 1754985600 — the token expiry is off by an hour.",
    ],
    [
      "a long numeric id",
      "The job id is 483920184720 and it has been stuck in queued for two hours now.",
    ],
    [
      "a version and a checksum",
      "Pinned to 1.2.30 after the sha 8891234567890 landed. Anyone else seeing this?",
    ],
    [
      "screaming constants",
      "Set MAX_RETRIES=3 and API_BASE_URL correctly, otherwise CI fails with ETIMEDOUT every time.",
    ],
    [
      "a fenced code block",
      "Try this:\n```\nSELECT id FROM users WHERE id = id AND id = id AND id = id;\n```\nDoes that help?",
    ],
    [
      "a stack trace",
      "Getting `NullPointerException` at `com.example.Foo.bar(Foo.java:42)` — full trace:\n    at com.example.Foo.bar\n    at com.example.Foo.baz\n    at com.example.Foo.qux",
    ],
    [
      "a well-sourced write-up",
      `I spent the week benchmarking our query layer and wanted to write up what I found, because a few
       of the results surprised me and I think they change how we should be thinking about the read
       path. The short version is that the index we added last quarter is doing much less work than we
       assumed, and most of the latency is coming from somewhere else entirely. References:
       https://example.com/a https://example.com/b https://example.com/c https://example.com/d
       https://example.com/e`,
    ],
    ["a plain question", "Has anyone got the dev container working on an M1 Mac?"],
    ["a single marketing-ish word", "We finally shipped the discount code feature for the store."],
    ["an empty string", ""],
    ["whitespace only", "   \n  "],
  ];

  it.each(legitimate)("does not block %s", (_label, text) => {
    expect(isBlocked(text)).toBe(false);
  });

  it("does not flag a bare ten-digit run as a phone number", () => {
    // The old pattern was /\+?[0-9]{10,12}/, which fired on all of these.
    expect(signalIds("epoch 1754985600")).not.toContain("phone-number");
    expect(signalIds("id 483920184720")).not.toContain("phone-number");
  });

  it("does not fire a keyword inside a longer word", () => {
    expect(signalIds("We use bettingham as our staging host name")).not.toContain("keywords");
  });

  it("does not treat a link whose path mentions t.me as a chat invite", () => {
    expect(signalIds("See https://example.com/blog/t.me-considered-harmful")).not.toContain(
      "suspicious-hosts",
    );
  });

  it("does not count repeated identifiers in code as repetitive words", () => {
    const text =
      "```\nconst a = a; const a = a; const a = a; const a = a; const a = a; const a = a;\n```";

    expect(signalIds(text)).not.toContain("repeated-words");
  });
});

describe("analyzeSpam — obvious spam is blocked", () => {
  const spam: [string, string][] = [
    ["a plain advert", "BUY NOW for guaranteed profit, click here!"],
    ["a chat invite", "Free money every day, join our telegram group: https://t.me/scamchannel"],
    ["a shortener plus keywords", "Crypto giveaway! Click here https://bit.ly/xyz to earn fast."],
    [
      "a contact number plus keywords",
      "Unlimited followers, cheap price. DM for info or call +1 555 867 5309.",
    ],
  ];

  it.each(spam)("blocks %s", (_label, text) => {
    expect(isBlocked(text)).toBe(true);
  });
});

describe("analyzeSpam — obfuscation no longer gets through", () => {
  const evasions: [string, string][] = [
    ["leetspeak", "fr33 m0n3y here, cl1ck h3r3 for a crypt0 giv3away!"],
    ["spaced-out letters", "b u y  n o w and get f r e e  m o n e y today"],
    ["zero-width separators", "buy​ now and get free​ money right away"],
    ["fullwidth characters", "ＢＵＹ ＮＯＷ for ＦＲＥＥ ＭＯＮＥＹ"],
    ["mathematical bold", "𝐛𝐮𝐲 𝐧𝐨𝐰 for 𝐟𝐫𝐞𝐞 𝐦𝐨𝐧𝐞𝐲"],
    ["strikethrough combining marks", "b̶u̶y̶ n̶o̶w̶ — free money!"],
  ];

  it.each(evasions)("catches %s", (_label, text) => {
    expect(isBlocked(text)).toBe(true);
  });

  it("catches a homoglyph shortener host", () => {
    // U+2024 instead of a full stop, which renders identically.
    expect(signalIds("Join now https://t․me/scamchannel")).toContain("suspicious-hosts");
  });
});

describe("analyzeSpam — phone numbers", () => {
  it("recognises an international number", () => {
    expect(signalIds("call +1 555 867 5309")).toContain("phone-number");
  });

  it("recognises a grouped number", () => {
    expect(signalIds("reach me on 555-867-5309")).toContain("phone-number");
  });

  it("recognises a number with parentheses", () => {
    expect(signalIds("reach me on (555) 867-5309")).toContain("phone-number");
  });

  it("does not recognise a semver string", () => {
    expect(signalIds("upgraded to 10.2.30 last night")).not.toContain("phone-number");
  });

  it("does not recognise a bare digit run", () => {
    expect(signalIds("the id is 5558675309")).not.toContain("phone-number");
  });

  it("is not enough on its own to block a post", () => {
    // Sharing a phone number is not spam by itself; plenty of legitimate posts
    // do it. It only matters alongside something else.
    expect(isBlocked("You can reach me on +1 555 867 5309 if that is easier.")).toBe(false);
  });
});

describe("analyzeSpam — scoring", () => {
  it("caps the keyword signal so three phrases cannot max the score", () => {
    const result = analyzeSpam("buy now, click here, cheap price");
    const keywords = result.signals.find((s) => s.id === "keywords");

    expect(keywords?.weight).toBeLessThanOrEqual(0.6);
  });

  it("never exceeds 1", () => {
    const result = analyzeSpam(
      "BUY NOW!!! free money, click here, cheap price, casino, betting, " +
        "guaranteed profit, https://bit.ly/a https://t.me/b https://wa.me/c " +
        "https://cutt.ly/d call +1 555 867 5309 aaaaaaaaaa",
    );

    expect(result.score).toBeLessThanOrEqual(1);
    expect(result.isSpam).toBe(true);
  });

  it("never goes below 0", () => {
    expect(analyzeSpam("A perfectly ordinary sentence about work.").score).toBeGreaterThanOrEqual(
      0,
    );
  });

  it("agrees with the exported threshold", () => {
    const result = analyzeSpam("BUY NOW for guaranteed profit, click here!");

    expect(result.isSpam).toBe(result.score >= SPAM_THRESHOLD);
  });

  it("reports one reason per signal", () => {
    const result = analyzeSpam("Free money! Join https://t.me/scam now.");

    expect(result.reasons).toHaveLength(result.signals.length);
    expect(result.reasons.every((r) => r.length > 0)).toBe(true);
  });

  it("exposes the normalised text that was matched against", () => {
    const result = analyzeSpam("fr33 m0n3y");

    // So a disputed block can be explained rather than argued about.
    expect(result.normalizedText).toContain("free money");
  });

  it("scores an empty post at zero with no signals", () => {
    const result = analyzeSpam("");

    expect(result).toMatchObject({ isSpam: false, score: 0, reasons: [], signals: [] });
  });
});

describe("analyzeSpam — shape rules", () => {
  it("flags shouting in prose", () => {
    expect(signalIds("THIS IS AN ENORMOUS ANNOUNCEMENT AND YOU MUST ALL READ IT NOW")).toContain(
      "shouting",
    );
  });

  it("does not flag shouting in something that reads like code", () => {
    expect(
      signalIds("MAX_RETRIES = 3; API_BASE_URL = ENV_PROD; TIMEOUT_MS = 500; RETRY_CAP = 8;"),
    ).not.toContain("shouting");
  });

  it("does not flag a short all-caps phrase", () => {
    expect(signalIds("LGTM")).not.toContain("shouting");
  });

  it("flags stretched-out characters", () => {
    expect(signalIds("looooooook at this")).toContain("repeated-characters");
  });

  it("flags genuinely repetitive prose", () => {
    expect(signalIds("free free free free free free free free free free free free free")).toContain(
      "repeated-words",
    );
  });

  it("does not flag repetition in a short post", () => {
    expect(signalIds("free free free")).not.toContain("repeated-words");
  });
});
