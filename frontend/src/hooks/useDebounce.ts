import { useEffect, useState } from "react";

/**
 * Debounce a rapidly-changing value (e.g. a search input).
 *
 * Returns a value that only updates after `delay` ms have elapsed
 * without a change.  The leading value is emitted immediately so the
 * first keystroke is not visually delayed.
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
