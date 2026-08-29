/**
 * DevLink Typography System
 *
 * Provides a consistent, semantic typography scale across the application.
 * All components support an `as` prop for semantic HTML (polymorphic rendering).
 *
 * Scale:
 *   TypoHero     — Landing / marketing hero headline
 *   TypoHeading  — Primary page / section title (h1, h2)
 *   TypoSection  — Sub-section label (h3, h4)
 *   TypoCard     — Card title / list item header (h5, h6)
 *   TypoBody     — Main prose text (p)
 *   TypoCaption  — Supplementary / metadata text (span, small)
 *
 * Usage:
 *   <TypoHero>Where builders connect</TypoHero>
 *   <TypoHeading as="h2">My Projects</TypoHeading>
 *   <TypoSection>Active Contributors</TypoSection>
 *   <TypoCard>Project Alpha</TypoCard>
 *   <TypoBody>Full-stack React and FastAPI developer.</TypoBody>
 *   <TypoCaption>Updated 3 days ago</TypoCaption>
 */

import { type ElementType, type ReactNode, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

// ─── Shared polymorphic helper ────────────────────────────────────────────────

type PolymorphicProps<E extends ElementType = ElementType> = {
  as?: E;
  children?: ReactNode;
  className?: string;
} & Omit<HTMLAttributes<HTMLElement>, "as">;

// ─── TypoHero ─────────────────────────────────────────────────────────────────
/**
 * Hero — largest typographic unit, for landing / marketing sections.
 * Renders as <h1> by default.
 *
 * Visual: 3xl–5xl, bold, tight leading, gradient-optional.
 */
export function TypoHero({
  as: Tag = "h1",
  children,
  className,
  ...props
}: PolymorphicProps<"h1" | "h2" | "h3" | "div">) {
  return (
    <Tag
      className={cn(
        // Base
        "font-extrabold leading-tight tracking-tight text-foreground",
        // Fluid size: clamp between 2.25rem (36px) and 3.75rem (60px)
        "text-4xl sm:text-5xl",
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

// ─── TypoHeading ─────────────────────────────────────────────────────────────
/**
 * Heading — primary page / section title.
 * Renders as <h2> by default. Use for page titles and major section breaks.
 *
 * Visual: 2xl–3xl, bold, tight leading.
 */
export function TypoHeading({
  as: Tag = "h2",
  children,
  className,
  ...props
}: PolymorphicProps<"h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "div" | "p" | "span">) {
  return (
    <Tag
      className={cn(
        "font-bold leading-tight tracking-tight text-foreground",
        "text-2xl sm:text-3xl",
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

// ─── TypoSection ─────────────────────────────────────────────────────────────
/**
 * Section — sub-section title within a page or card group.
 * Renders as <h3> by default.
 *
 * Visual: xl–2xl, semibold.
 */
export function TypoSection({
  as: Tag = "h3",
  children,
  className,
  ...props
}: PolymorphicProps<"h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "div" | "p" | "span">) {
  return (
    <Tag
      className={cn("font-semibold leading-snug text-foreground", "text-xl sm:text-2xl", className)}
      {...props}
    >
      {children}
    </Tag>
  );
}

// ─── TypoCard ─────────────────────────────────────────────────────────────────
/**
 * Card — card title, list item heading, or highlight label.
 * Renders as <h4> by default.
 *
 * Visual: base–lg, semibold, slightly tighter line height.
 */
export function TypoCard({
  as: Tag = "h4",
  children,
  className,
  ...props
}: PolymorphicProps<"h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "div" | "p" | "span">) {
  return (
    <Tag
      className={cn(
        "font-semibold leading-snug text-foreground",
        "text-base sm:text-lg",
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

// ─── TypoBody ─────────────────────────────────────────────────────────────────
/**
 * Body — standard readable prose text.
 * Renders as <p> by default.
 *
 * Visual: base, normal weight, relaxed leading for readability.
 */
export function TypoBody({
  as: Tag = "p",
  children,
  className,
  ...props
}: PolymorphicProps<"p" | "div" | "span" | "li" | "article" | "section">) {
  return (
    <Tag
      className={cn(
        "font-normal leading-relaxed text-foreground",
        "text-sm sm:text-base",
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

// ─── TypoCaption ─────────────────────────────────────────────────────────────
/**
 * Caption — supplementary, metadata, or annotation text.
 * Renders as <span> by default.
 *
 * Visual: xs–sm, muted foreground, tighter leading.
 */
export function TypoCaption({
  as: Tag = "span",
  children,
  className,
  ...props
}: PolymorphicProps<"span" | "p" | "small" | "div" | "time" | "label">) {
  return (
    <Tag
      className={cn(
        "font-normal leading-tight text-muted-foreground",
        "text-xs sm:text-sm",
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}
