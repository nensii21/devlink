import type { Variants, TargetAndTransition } from "framer-motion";
import { useReducedMotion } from "framer-motion";

export const STAGGER_DELAY = 0.05;

export const cardEntrance: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.1, 0.25, 1],
      delay: i * STAGGER_DELAY,
    },
  }),
};

export const cardHover: TargetAndTransition = {
  y: -3,
  scale: 1.02,
  transition: { duration: 0.2, ease: "easeOut" as const },
};

export const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: STAGGER_DELAY },
  },
};

export function useCardAnimation(index: number = 0) {
  const shouldReduceMotion = useReducedMotion();

  return {
    variants: shouldReduceMotion ? undefined : cardEntrance,
    initial: shouldReduceMotion ? undefined : "hidden",
    animate: shouldReduceMotion ? undefined : "visible",
    custom: index,
    whileHover: shouldReduceMotion ? undefined : cardHover,
  };
}
