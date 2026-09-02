"use client";

import { useEffect } from "react";

export interface ShortcutBinding {
  /** Human description for the help modal. */
  description: string;
  /** Key combo expressed as a string (e.g. " ", "j", "ArrowLeft", "Mod+z"). */
  combo: string;
  /** Handler — receives the original KeyboardEvent so callers can prevent default if needed. */
  handler: (e: KeyboardEvent) => void;
  /**
   * If true, the shortcut fires even when an input/textarea/contenteditable
   * has focus. Defaults to false (suppressed while typing).
   */
  allowInInput?: boolean;
}

function normalize(combo: string): string {
  return combo
    .toLowerCase()
    .split("+")
    .map((p) => (p === "mod" || p === "cmd" || p === "ctrl" || p === "meta" ? "mod" : p.trim()))
    .sort()
    .join("+");
}

function eventMatches(e: KeyboardEvent, combo: string): boolean {
  const want = normalize(combo);
  const got: string[] = [];
  if (e.ctrlKey || e.metaKey) got.push("mod");
  if (e.shiftKey) got.push("shift");
  if (e.altKey) got.push("alt");
  // `e.key` for letters is lowercase; for arrows/space we use lowercased values.
  const key = e.key === " " ? "space" : e.key.toLowerCase();
  got.push(key);
  return got.sort().join("+") === want;
}

/**
 * Registers a set of global keyboard shortcuts. Call once per page; pass the
 * array of bindings you want active. Shortcuts that use letters or punctuation
 * are intentionally suppressed while an input/textarea/contenteditable has focus,
 * unless `allowInInput` is set.
 */
export function useShortcuts(bindings: ShortcutBinding[]): void {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const inEditable =
        !!target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);

      for (const b of bindings) {
        if (!eventMatches(e, b.combo)) continue;
        if (inEditable && !b.allowInInput) continue;
        b.handler(e);
        // Stop propagation so the same combo doesn't fire on the next matching binding.
        e.preventDefault();
        return;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [bindings]);
}
