"use client";

import { useState } from "react";
import { Button, Modal } from "@/components/ui";
import { useShortcuts, type ShortcutBinding } from "@/lib/useShortcuts";
import { theme } from "@/lib/theme";

/**
 * Keyboard shortcuts help modal.
 *
 * Renders a small floating "?" button that opens a modal listing all currently
 * active shortcuts. Bindings are passed in (typically the same array given to
 * `useShortcuts`) so the modal stays in sync with what's actually wired up.
 *
 * Includes a built-in `?` key binding (with `allowInInput: false`) to open the modal.
 */
export function ShortcutsHelp({ bindings }: { bindings: ShortcutBinding[] }) {
  const [open, setOpen] = useState(false);

  useShortcuts([
    { combo: "?", description: "Mở danh sách phím tắt", handler: () => setOpen(true) },
    { combo: "Escape", description: "Đóng", handler: () => setOpen(false), allowInInput: true },
  ]);

  // Detect Mac vs Windows/Linux for the "Mod" key label.
  const isMac =
    typeof navigator !== "undefined" &&
    /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent);
  const modLabel = isMac ? "⌘" : "Ctrl";

  const rendered = bindings.map((b) => {
    // Normalize "Mod+" for display only.
    const pretty = b.combo
      .split("+")
      .map((p) => {
        const k = p.trim();
        if (k === "Mod" || k === "mod") return modLabel;
        if (k === "Shift") return "⇧";
        if (k === "Alt") return isMac ? "⌥" : "Alt";
        if (k === "ArrowLeft") return "←";
        if (k === "ArrowRight") return "→";
        if (k === "ArrowUp") return "↑";
        if (k === "ArrowDown") return "↓";
        if (k === " ") return "Space";
        return k.charAt(0).toUpperCase() + k.slice(1);
      })
      .join(" + ");
    return { key: pretty, desc: b.description };
  });

  return (
    <>
      <Button
        size="sm"
        variant="ghost"
        onClick={() => setOpen(true)}
        title="Phím tắt (?)"
        aria-label="Phím tắt"
        style={{
          padding: "2px 8px",
          fontSize: 12,
          color: theme.textMuted,
        }}
      >
        ⌨ Phím tắt
      </Button>
      <Modal open={open} onClose={() => setOpen(false)} title="Phím tắt bàn phím" width={460}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <p style={{ fontSize: 12, color: theme.textMuted, margin: 0 }}>
            Nhấn <kbd>?</kbd> bất kỳ lúc nào để mở cửa sổ này.
          </p>
          {rendered.length === 0 ? (
            <p style={{ fontSize: 13, color: theme.textMuted, textAlign: "center", padding: 16 }}>
              Chưa có phím tắt nào được đăng ký.
            </p>
          ) : (
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              {rendered.map((r, i) => (
                <li
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px 8px",
                    borderRadius: 4,
                    background: i % 2 === 0 ? theme.bgElevated : "transparent",
                  }}
                >
                  <span style={{ fontSize: 13 }}>{r.desc}</span>
                  <kbd
                    style={{
                      fontFamily: "ui-monospace, monospace",
                      fontSize: 11,
                      background: theme.bgPanel,
                      border: `1px solid ${theme.border}`,
                      borderRadius: 4,
                      padding: "2px 8px",
                      color: theme.text,
                    }}
                  >
                    {r.key}
                  </kbd>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Modal>
    </>
  );
}
