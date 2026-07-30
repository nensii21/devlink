/**
 * DevLink — Professional Motion System
 *
 * Centralised animation configuration for Framer Motion.
 * All animation variants live here so they stay consistent across the app.
 *
 * Respects `prefers-reduced-motion` via the `useReducedMotion()` hook from
 * Framer Motion — consumers should call that hook and pass `reducedMotion`
 * variants when the user prefers reduced motion.
 */

import type { Variants } from "framer-motion";

// ─── Duration tokens ──────────────────────────────────────────────────────────
export const DURATION = {
  fast: 0.15,
  base: 0.25,
  slow: 0.4,
  xslow: 0.6,
} as const;

// ─── Easing tokens ────────────────────────────────────────────────────────────
export const EASE = {
  /** Standard ease-in-out for most UI transitions */
  standard: [0.4, 0, 0.2, 1] as [number, number, number, number],
  /** Enters quickly, eases out — for elements entering the screen */
  decelerate: [0, 0, 0.2, 1] as [number, number, number, number],
  /** Eases in, exits sharply — for elements leaving the screen */
  accelerate: [0.4, 0, 1, 1] as [number, number, number, number],
  /** Spring feel for interactive surfaces */
  spring: { type: "spring", stiffness: 300, damping: 24 } as const,
  /** Gentle spring for modals & drawers */
  springGentle: { type: "spring", stiffness: 200, damping: 26 } as const,
} as const;

// ─── Page / route transitions ─────────────────────────────────────────────────
/** Slide + fade on page enter/exit — use with AnimatePresence + mode="wait" */
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATION.base, ease: EASE.decelerate },
  },
  exit: {
    opacity: 0,
    y: -6,
    transition: { duration: DURATION.fast, ease: EASE.accelerate },
  },
};

/** Instant variants for reduced-motion users */
export const pageVariantsReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0 } },
  exit: { opacity: 0, transition: { duration: 0 } },
};

// ─── Fade variants ────────────────────────────────────────────────────────────
/** Simple opacity fade — general purpose */
export const fadeVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: DURATION.base, ease: EASE.standard } },
  exit: { opacity: 0, transition: { duration: DURATION.fast, ease: EASE.accelerate } },
};

export const fadeVariantsReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0 } },
  exit: { opacity: 0, transition: { duration: 0 } },
};

// ─── Modal animations ─────────────────────────────────────────────────────────
/** Scale + fade for dialog / sheet content */
export const modalContentVariants: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 8 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: EASE.springGentle,
  },
  exit: {
    opacity: 0,
    scale: 0.97,
    y: 4,
    transition: { duration: DURATION.fast, ease: EASE.accelerate },
  },
};

/** Backdrop blur fade */
export const backdropVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: DURATION.base, ease: EASE.standard } },
  exit: { opacity: 0, transition: { duration: DURATION.fast, ease: EASE.accelerate } },
};

export const modalVariantsReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0 } },
  exit: { opacity: 0, transition: { duration: 0 } },
};

// ─── Notification / toast animations ─────────────────────────────────────────
/** Slide in from the right + fade */
export const notificationVariants: Variants = {
  initial: { opacity: 0, x: 40, scale: 0.96 },
  animate: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: EASE.spring,
  },
  exit: {
    opacity: 0,
    x: 40,
    scale: 0.96,
    transition: { duration: DURATION.fast, ease: EASE.accelerate },
  },
};

export const notificationVariantsReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0 } },
  exit: { opacity: 0, transition: { duration: 0 } },
};

// ─── Hover elevation ─────────────────────────────────────────────────────────
/**
 * Spread these onto a `motion.*` element for a subtle lift on hover.
 *
 * @example
 * <motion.div whileHover={hoverElevation.whileHover} whileTap={hoverElevation.whileTap}>
 */
export const hoverElevation = {
  whileHover: {
    y: -2,
    scale: 1.01,
    transition: { duration: DURATION.fast, ease: EASE.decelerate },
  },
  whileTap: { y: 0, scale: 0.98, transition: { duration: DURATION.fast, ease: EASE.accelerate } },
};

export const hoverElevationReduced = {
  whileHover: {},
  whileTap: {},
};

// ─── List stagger ─────────────────────────────────────────────────────────────
/** Container: staggers children in sequence */
export const listContainerVariants: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.06, delayChildren: 0.05 } },
};

/** Child item: slides up + fades */
export const listItemVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATION.base, ease: EASE.decelerate },
  },
};

export const listItemVariantsReduced: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0 } },
};

// ─── Slide variants (sidebar, drawers) ───────────────────────────────────────
export const slideFromLeftVariants: Variants = {
  initial: { opacity: 0, x: -16 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: DURATION.slow, ease: EASE.decelerate },
  },
  exit: {
    opacity: 0,
    x: -16,
    transition: { duration: DURATION.fast, ease: EASE.accelerate },
  },
};

export const slideFromRightVariants: Variants = {
  initial: { opacity: 0, x: 16 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: DURATION.slow, ease: EASE.decelerate },
  },
  exit: {
    opacity: 0,
    x: 16,
    transition: { duration: DURATION.fast, ease: EASE.accelerate },
  },
};
