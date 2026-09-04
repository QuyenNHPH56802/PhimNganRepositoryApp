/**
 * Accessibility utilities.
 *
 * - `useRovingTabIndex` for arrow-key navigation inside list-like grids
 *   (e.g. speaker list, translation segments).
 * - `useSkipLink` registers a single "Skip to content" anchor on mount so
 *   keyboard users can bypass the AppShell sidebar.
 * - `visuallyHidden` style helper for screen-reader-only labels.
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Returns a `style` object that hides content visually but keeps it
 * available to screen readers. Apply to icon-only buttons that need a label.
 */
export const visuallyHidden: React.CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  margin: -1,
  padding: 0,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
  border: 0,
};

/**
 * Arrow-key / Home / End roving tab-index loop.
 *
 * Returns a `containerProps` object to spread on the parent, plus an
 * `itemProps(index)` helper for each focusable item.
 *
 * Usage:
 *   const { containerProps, itemProps } = useRovingTabIndex({ itemCount: 5 });
 *   return (
 *     <div {...containerProps}>
 *       {items.map((it, i) => (
 *         <button key={it.id} {...itemProps(i)}>{it.label}</button>
 *       ))}
 *     </div>
 *   );
 */
export function useRovingTabIndex({
  itemCount,
  orientation = "vertical",
  loop = true,
}: {
  itemCount: number;
  orientation?: "vertical" | "horizontal" | "both";
  loop?: boolean;
}) {
  const [activeIndex, setActiveIndex] = useState(0);

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const isVertical = orientation !== "horizontal";
      const isHorizontal = orientation !== "vertical";

      let next = activeIndex;

      if (isVertical && e.key === "ArrowDown") next = activeIndex + 1;
      else if (isVertical && e.key === "ArrowUp") next = activeIndex - 1;
      else if (isHorizontal && e.key === "ArrowRight") next = activeIndex + 1;
      else if (isHorizontal && e.key === "ArrowLeft") next = activeIndex - 1;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = itemCount - 1;
      else return;

      if (next < 0) next = loop ? itemCount - 1 : 0;
      if (next >= itemCount) next = loop ? 0 : itemCount - 1;

      e.preventDefault();
      setActiveIndex(next);

      // Move actual focus to the matching DOM node.
      const root = (e.currentTarget as HTMLElement | null);
      const target = root?.querySelector<HTMLElement>(`[data-roving-index="${next}"]`);
      target?.focus();
    },
    [activeIndex, itemCount, loop, orientation],
  );

  const containerProps: React.HTMLAttributes<HTMLDivElement> = {
    role: orientation === "horizontal" ? "tablist" : "listbox",
    onKeyDown: onKeyDown as unknown as React.KeyboardEventHandler<HTMLDivElement>,
  };

  const itemProps = (index: number): React.HTMLAttributes<HTMLElement> => ({
    "data-roving-index": index,
    tabIndex: index === activeIndex ? 0 : -1,
  });

  return { containerProps, itemProps, activeIndex, setActiveIndex };
}

/**
 * Registers a "Skip to main content" link on mount.
 *
 * Renders an anchor that becomes visible only when focused, anchored before
 * the page main content. Useful for keyboard users who don't want to tab
 * through the sidebar on every page.
 */
export function useSkipLink(targetId = "main-content") {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      // Alt+S (or Ctrl+Alt+S) jumps focus to skip link.
      if (e.altKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        const link = document.getElementById("skip-to-main");
        link?.focus();
        link?.click();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  return {
    href: `#${targetId}`,
    id: "skip-to-main",
    className: "skip-to-main",
  };
}

/**
 * Returns true if the user has requested reduced motion via OS settings.
 * Updates if the user toggles the preference during a session.
 */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(mql.matches);
    update();
    mql.addEventListener("change", update);
    return () => mql.removeEventListener("change", update);
  }, []);
  return reduced;
}

/**
 * Announce a message to screen readers via an aria-live region.
 * Pass the same element reference back across renders; the helper handles
 * deduplication so re-renders don't spam announcements.
 */
export function useLiveRegion() {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (ref.current) return;
    // Create a hidden live region once on mount.
    const el = document.createElement("div");
    el.setAttribute("aria-live", "polite");
    el.setAttribute("aria-atomic", "true");
    Object.assign(el.style, visuallyHidden);
    document.body.appendChild(el);
    ref.current = el;
    return () => {
      el.remove();
      ref.current = null;
    };
  }, []);

  return useCallback((message: string) => {
    if (!ref.current) return;
    // Clear then set after a tick so identical consecutive messages still
    // re-announce.
    ref.current.textContent = "";
    setTimeout(() => {
      if (ref.current) ref.current.textContent = message;
    }, 50);
  }, []);
}
