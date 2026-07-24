import { describe, it, expect } from "vitest";
import { highlightMatches, type HighlightSegment } from "@/lib/highlight";

describe("highlightMatches", () => {
  it("returns single non-highlighted segment for empty query", () => {
    const result = highlightMatches("hello world", "");
    expect(result).toEqual([{ text: "hello world", highlighted: false }]);
  });

  it("returns single non-highlighted segment for whitespace-only query", () => {
    const result = highlightMatches("hello world", "   ");
    expect(result).toEqual([{ text: "hello world", highlighted: false }]);
  });

  it("highlights a single exact match", () => {
    const result = highlightMatches("hello world", "hello");
    expect(result).toEqual([
      { text: "hello", highlighted: true },
      { text: " world", highlighted: false },
    ]);
  });

  it("performs case-insensitive matching", () => {
    const result = highlightMatches("Hello World", "hello");
    expect(result).toEqual([
      { text: "Hello", highlighted: true },
      { text: " World", highlighted: false },
    ]);
  });

  it("highlights partial-word matches", () => {
    const result = highlightMatches("JavaScript", "script");
    expect(result).toEqual([
      { text: "Java", highlighted: false },
      { text: "Script", highlighted: true },
    ]);
  });

  it("highlights multiple matches in the same string", () => {
    const result = highlightMatches("foo bar foo baz foo", "foo");
    expect(result).toEqual([
      { text: "foo", highlighted: true },
      { text: " bar ", highlighted: false },
      { text: "foo", highlighted: true },
      { text: " baz ", highlighted: false },
      { text: "foo", highlighted: true },
    ]);
  });

  it("returns non-highlighted segment when no match", () => {
    const result = highlightMatches("hello world", "xyz");
    expect(result).toEqual([{ text: "hello world", highlighted: false }]);
  });

  it("escapes special regex characters", () => {
    const result = highlightMatches("price is $10.00 (USD)", "$10.00");
    expect(result).toEqual([
      { text: "price is ", highlighted: false },
      { text: "$10.00", highlighted: true },
      { text: " (USD)", highlighted: false },
    ]);
  });

  it("handles text with parentheses", () => {
    const result = highlightMatches("React (with hooks)", "hooks");
    expect(result).toEqual([
      { text: "React (with ", highlighted: false },
      { text: "hooks", highlighted: true },
      { text: ")", highlighted: false },
    ]);
  });

  it("handles unicode text", () => {
    const result = highlightMatches("Namaste दुनिया", "दुनिया");
    expect(result).toEqual([
      { text: "Namaste ", highlighted: false },
      { text: "दुनिया", highlighted: true },
    ]);
  });

  it("handles emoji in text", () => {
    const result = highlightMatches("Hello 🌍 World", "🌍");
    expect(result).toEqual([
      { text: "Hello ", highlighted: false },
      { text: "🌍", highlighted: true },
      { text: " World", highlighted: false },
    ]);
  });

  it("handles empty text", () => {
    const result = highlightMatches("", "hello");
    expect(result).toEqual([{ text: "", highlighted: false }]);
  });

  it("handles both empty text and query", () => {
    const result = highlightMatches("", "");
    expect(result).toEqual([{ text: "", highlighted: false }]);
  });
});
