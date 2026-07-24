export interface HighlightSegment {
  text: string;
  highlighted: boolean;
}

const ESCAPE_RE = /[.*+?^${}()|[\]\\]/g;

function escapeRegex(s: string): string {
  return s.replace(ESCAPE_RE, "\\$&");
}

/**
 * Split `text` into segments marking which parts match the search `query`.
 *
 * - Case-insensitive matching
 * - Partial-word matches (matches anywhere inside a word)
 * - Multiple non-overlapping matches
 * - Empty / whitespace-only query returns a single non-highlighted segment
 */
export function highlightMatches(text: string, query: string): HighlightSegment[] {
  const trimmed = query.trim();
  if (!trimmed) return [{ text, highlighted: false }];
  if (!text) return [{ text: "", highlighted: false }];

  const pattern = new RegExp(escapeRegex(trimmed), "gi");
  const segments: HighlightSegment[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(pattern)) {
    const matchStart = match.index!;
    if (matchStart > lastIndex) {
      segments.push({ text: text.slice(lastIndex, matchStart), highlighted: false });
    }
    segments.push({ text: match[0], highlighted: true });
    lastIndex = matchStart + match[0].length;
  }

  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex), highlighted: false });
  }

  return segments.length > 0 ? segments : [{ text, highlighted: false }];
}
