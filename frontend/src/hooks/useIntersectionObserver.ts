import { useEffect, useRef, useCallback } from "react";

export function useIntersectionObserver(
  onIntersect: () => void,
  enabled: boolean,
): (node: Element | null) => void {
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    return () => {
      observerRef.current?.disconnect();
    };
  }, []);

  return useCallback(
    (node: Element | null) => {
      observerRef.current?.disconnect();

      if (!enabled || !node) return;

      observerRef.current = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            onIntersect();
          }
        },
        { rootMargin: "200px" },
      );

      observerRef.current.observe(node);
    },
    [enabled, onIntersect],
  );
}
