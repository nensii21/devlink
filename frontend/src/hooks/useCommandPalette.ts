"use client";

import * as React from "react";

type UseCommandPaletteResult = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  toggle: () => void;
};

function isMacLikePlatform(): boolean {
  const platform = navigator.platform?.toLowerCase?.() ?? "";
  const userAgent = navigator.userAgent?.toLowerCase?.() ?? "";
  return platform.includes("mac") || userAgent.includes("mac os");
}

export function useCommandPalette(): UseCommandPaletteResult {
  const [open, setOpen] = React.useState<boolean>(false);

  const toggle = React.useCallback(() => {
    setOpen((prev) => !prev);
  }, []);

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isMac = isMacLikePlatform();
      const kPressed = event.key.toLowerCase() === "k";

      const shouldTrigger = isMac ? event.metaKey && kPressed : event.ctrlKey && kPressed;
      if (!shouldTrigger) return;

      event.preventDefault();
      event.stopPropagation();
      toggle();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [toggle]);

  return { open, setOpen, toggle };
}
