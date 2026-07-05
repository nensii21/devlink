"use client";

import * as React from "react";

type CommandPaletteGroup = "pages" | "projects" | "developers";

export type CommandPaletteItemBase = {
  id: string;
  title: string;
  description?: string;
  group: CommandPaletteGroup;
};

type FlattenedResult<TItem extends CommandPaletteItemBase> =
  | { type: "header"; id: string; label: string; group: CommandPaletteGroup }
  | { type: "item"; item: TItem };

export type CommandPaletteProps<TItem extends CommandPaletteItemBase> = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  results: Array<{
    group: CommandPaletteGroup;
    items: TItem[];
  }>;
  onSelect: (item: TItem) => void;
};

function getGroupLabel(group: CommandPaletteGroup): string {
  switch (group) {
    case "pages":
      return "Pages";
    case "projects":
      return "Projects";
    case "developers":
      return "Developers";
  }
}

export function CommandPalette<TItem extends CommandPaletteItemBase>(
  props: CommandPaletteProps<TItem>,
): React.ReactElement {
  const { open, onOpenChange, results, onSelect } = props;

  const searchInputRef = React.useRef<HTMLInputElement | null>(null);
  const [highlightedIndex, setHighlightedIndex] = React.useState<number>(-1);

  const flattened = React.useMemo<FlattenedResult<TItem>[]>(() => {
    const acc: FlattenedResult<TItem>[] = [];

    for (const group of results) {
      acc.push({
        type: "header",
        id: `header-${group.group}`,
        label: getGroupLabel(group.group),
        group: group.group,
      });

      for (const item of group.items) {
        acc.push({ type: "item", item });
      }
    }

    return acc;
  }, [results]);

  const itemIndices = React.useMemo<number[]>(() => {
    const indices: number[] = [];
    for (let i = 0; i < flattened.length; i += 1) {
      if (flattened[i].type === "item") indices.push(i);
    }
    return indices;
  }, [flattened]);

  const highlightedItemIndexInItems = React.useMemo<number>(() => {
    if (highlightedIndex < 0) return -1;
    const pos = itemIndices.indexOf(highlightedIndex);
    return pos;
  }, [highlightedIndex, itemIndices]);

  const focusSearch = React.useCallback(() => {
    searchInputRef.current?.focus();
  }, []);

  React.useEffect(() => {
    if (!open) return;
    focusSearch();

    const firstItemIndex = itemIndices[0] ?? -1;
    setHighlightedIndex(firstItemIndex);
  }, [open, focusSearch, itemIndices]);

  const close = React.useCallback(() => {
    onOpenChange(false);
  }, [onOpenChange]);

  const onBackdropMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) close();
  };

  const selectedItem = React.useMemo<TItem | null>(() => {
    if (highlightedIndex < 0) return null;
    const entry = flattened[highlightedIndex];
    if (!entry || entry.type !== "item") return null;
    return entry.item;
  }, [flattened, highlightedIndex]);

  const moveHighlight = React.useCallback(
    (direction: 1 | -1) => {
      if (itemIndices.length === 0) return;

      const currentPos = highlightedItemIndexInItems;
      const nextPos =
        currentPos === -1
          ? direction === 1
            ? 0
            : itemIndices.length - 1
          : (currentPos + direction + itemIndices.length) % itemIndices.length;

      setHighlightedIndex(itemIndices[nextPos] ?? -1);
    },
    [itemIndices, highlightedItemIndexInItems],
  );

  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveHighlight(1);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveHighlight(-1);
      return;
    }

    if (event.key === "Tab") {
      event.preventDefault();
      moveHighlight(event.shiftKey ? -1 : 1);
      return;
    }

    if (event.key === "Enter") {
      if (!selectedItem) return;
      event.preventDefault();
      onSelect(selectedItem);
      close();
    }
  };

  if (!open) return <React.Fragment />;

  return (
    <div
      className="fixed inset-0 z-50"
      role="presentation"
      onMouseDown={onBackdropMouseDown}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" role="presentation" />

      <div
        className={
          "relative mx-auto w-full px-3 sm:px-0 sm:flex sm:justify-center" +
          " sm:items-start"
        }
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
          className={
            "mt-[15vh] w-full sm:w-auto sm:max-w-xl min-w-0 rounded-xl border border-border bg-background shadow-2xl" +
            " focus:outline-none"
          }
          tabIndex={-1}
          onKeyDown={onKeyDown}
        >
          <div className="p-3 sm:p-4">
            <input
              ref={searchInputRef}
              type="search"
              placeholder="Search…"
              className={
                "min-h-[44px] w-full rounded-lg border border-input bg-background px-3 text-sm text-foreground" +
                " placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              }
              aria-label="Search"
            />
          </div>

          <div className="px-2 pb-2 sm:px-3 sm:pb-3">
            <div
              role="listbox"
              aria-label="Command results"
              className="max-h-[60vh] overflow-y-auto rounded-lg"
            >
              <ul className="m-0 list-none p-0">
                {flattened.map((entry, index) => {
                  if (entry.type === "header") {
                    return (
                      <li
                        key={entry.id}
                        className="px-3 py-2 text-[12px] font-medium text-muted-foreground"
                        aria-hidden="true"
                      >
                        {entry.label}
                      </li>
                    );
                  }

                  const item = entry.item;
                  const isSelected = index === highlightedIndex;

                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={isSelected}
                        tabIndex={-1}
                        onMouseEnter={() => setHighlightedIndex(index)}
                        onClick={() => {
                          onSelect(item);
                          close();
                        }}
                        className={
                          "flex w-full min-h-[44px] cursor-pointer items-start gap-3 rounded-lg px-3 py-2 text-left" +
                          " transition-colors" +
                          (isSelected
                            ? " bg-accent text-accent-foreground"
                            : " hover:bg-muted/50 text-foreground")
                        }
                      >
                        <span className="mt-0.5 inline-flex h-2 w-2 shrink-0 rounded-full bg-muted-foreground/40" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-medium">{item.title}</span>
                          {item.description ? (
                            <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                              {item.description}
                            </span>
                          ) : null}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>

          <div className="px-3 pb-3 sm:px-4">
            <div className="flex flex-wrap items-center justify-between gap-2 text-[12px] text-muted-foreground">
              <span>Use ↑ ↓, Enter to select</span>
              <span>Esc to close</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

