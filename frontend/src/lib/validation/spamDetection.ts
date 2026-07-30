export interface SpamCheckResult {
  isSpam: boolean;
  score: number; // 0 to 1 (higher = more likely spam)
  reasons: string[];
}

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
  "work from home $",
];

const PHISHING_PATTERNS = [
  /bit\.ly\//i,
  /tinyurl\.com\//i,
  /t\.me\//i,
  /wa\.me\//i,
  /\+?[0-9]{10,12}/, // Raw phone numbers
];

/**
 * Analyzes text for spam markers using keyword analysis, link density,
 * repetitive character/word detection, and casing rules.
 */
export function analyzeSpam(text: string): SpamCheckResult {
  const reasons: string[] = [];
  let score = 0;
  const lowerText = text.toLowerCase();

  if (!text || text.trim().length === 0) {
    return { isSpam: false, score: 0, reasons: [] };
  }

  // 1. Check for spam keywords
  const matchedKeywords = SPAM_KEYWORDS.filter((keyword) => lowerText.includes(keyword));
  if (matchedKeywords.length > 0) {
    score += matchedKeywords.length * 0.35;
    reasons.push(`Contains potential spam phrasing: "${matchedKeywords.join('", "')}"`);
  }

  // 2. Check for suspicious shortened links or phone numbers
  const matchedPhishing = PHISHING_PATTERNS.filter((pattern) => pattern.test(text));
  if (matchedPhishing.length > 0) {
    score += matchedPhishing.length * 0.4;
    reasons.push("Contains suspicious link shorteners or contact numbers");
  }

  // 3. Link density check
  const urls = text.match(/https?:\/\/[^\s]+/g) || [];
  if (urls.length > 3) {
    score += 0.3;
    reasons.push("Excessive number of external links");
  }

  // 4. ALL CAPS check (for longer content)
  if (text.length > 20) {
    const capsCount = (text.match(/[A-Z]/g) || []).length;
    const letterCount = (text.match(/[a-zA-Z]/g) || []).length;
    if (letterCount > 0 && capsCount / letterCount > 0.6) {
      score += 0.25;
      reasons.push("Excessive use of capital letters");
    }
  }

  // 5. Repeated character/word check (e.g. "aaaaa" or "buy buy buy")
  if (/(.)\1{5,}/.test(text)) {
    score += 0.3;
    reasons.push("Repeated character patterns detected");
  }

  const words = lowerText.split(/\s+/);
  const wordSet = new Set(words);
  if (words.length > 8 && wordSet.size / words.length < 0.4) {
    score += 0.3;
    reasons.push("High degree of repetitive words");
  }

  const finalScore = Math.min(score, 1);
  return {
    isSpam: finalScore >= 0.5,
    score: finalScore,
    reasons,
  };
}
