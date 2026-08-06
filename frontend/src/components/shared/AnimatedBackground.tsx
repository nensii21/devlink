import { useEffect } from "react";
import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from "framer-motion";

/**
 * Decorative animated background used on the landing page hero.
 * Renders a few soft, blurred gradient blobs that float gently and
 * shift slightly with the mouse (parallax). Purely visual: it sits
 * behind the content, ignores clicks, and respects prefers-reduced-motion.
 */
export function AnimatedBackground() {
  const prefersReducedMotion = useReducedMotion();

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth the raw pointer position so the parallax feels fluid, not jumpy.
  const springX = useSpring(mouseX, { stiffness: 40, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 40, damping: 20 });

  const blobAX = useTransform(springX, [-0.5, 0.5], [-20, 20]);
  const blobAY = useTransform(springY, [-0.5, 0.5], [-20, 20]);
  const blobBX = useTransform(springX, [-0.5, 0.5], [15, -15]);
  const blobBY = useTransform(springY, [-0.5, 0.5], [15, -15]);

  useEffect(() => {
    if (prefersReducedMotion) return;

    function handlePointerMove(e: PointerEvent) {
      mouseX.set(e.clientX / window.innerWidth - 0.5);
      mouseY.set(e.clientY / window.innerHeight - 0.5);
    }

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, [prefersReducedMotion, mouseX, mouseY]);

  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        style={prefersReducedMotion ? undefined : { x: blobAX, y: blobAY }}
        className="animate-blob absolute -top-32 -left-24 h-[420px] w-[420px] rounded-full bg-primary/20 blur-[100px]"
      />
      <motion.div
        style={prefersReducedMotion ? undefined : { x: blobBX, y: blobBY }}
        className="animate-blob animation-delay-2000 absolute top-1/3 -right-24 h-[380px] w-[380px] rounded-full bg-info/20 blur-[100px]"
      />
      <motion.div
        style={prefersReducedMotion ? undefined : { x: blobAX, y: blobBY }}
        className="animate-blob animation-delay-4000 absolute bottom-0 left-1/3 h-[360px] w-[360px] rounded-full bg-success/10 blur-[100px]"
      />
    </div>
  );
}