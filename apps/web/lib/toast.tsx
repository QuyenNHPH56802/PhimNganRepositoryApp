"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { theme } from "@/lib/theme";

export type ToastTone = "info" | "success" | "warn" | "danger";

interface Toast {
  id: string;
  tone: ToastTone;
  message: string;
}

interface ToastContextValue {
  toast: (message: string, tone?: ToastTone) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const TONE_STYLES: Record<ToastTone, { background: string; color: string; border: string }> = {
  info: { background: "#0c4a6e", color: theme.accent, border: "#0369a1" },
  success: { background: "#052e16", color: theme.success, border: "#14532d" },
  warn: { background: "#422006", color: theme.warn, border: "#713f12" },
  danger: { background: "#450a0a", color: theme.danger, border: "#7f1d1d" },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, tone: ToastTone = "info") => {
      const id =
        typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `t-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      setItems((prev) => [...prev, { id, tone, message }]);
      // Auto-dismiss after 4s — keep the queue short so the stack doesn't pile up.
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  const value = useMemo<ToastContextValue>(() => ({ toast, dismiss }), [toast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport items={items} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

function ToastViewport({
  items,
  onDismiss,
}: {
  items: Toast[];
  onDismiss: (id: string) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div
      role="region"
      aria-label="Thông báo"
      style={{
        position: "fixed",
        bottom: 16,
        right: 16,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        zIndex: 2000,
        maxWidth: "min(420px, calc(100vw - 32px))",
      }}
    >
      {items.map((t) => {
        const style = TONE_STYLES[t.tone];
        return (
          <div
            key={t.id}
            role={t.tone === "danger" || t.tone === "warn" ? "alert" : "status"}
            style={{
              background: style.background,
              color: style.color,
              border: `1px solid ${style.border}`,
              borderRadius: 8,
              padding: "10px 12px",
              fontSize: 13,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 10,
              boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            }}
          >
            <span style={{ flex: 1 }}>{t.message}</span>
            <button
              onClick={() => onDismiss(t.id)}
              aria-label="Đóng thông báo"
              style={{
                background: "transparent",
                border: "none",
                color: style.color,
                cursor: "pointer",
                fontSize: 16,
                lineHeight: 1,
                padding: 0,
              }}
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Allow calling code in places without a provider (e.g. server components
    // — though useToast should always run on the client). Fall back to a
    // no-op so the caller doesn't have to gate each invocation.
    return {
      toast: (msg) => {
        if (typeof console !== "undefined") console.warn("[toast]", msg);
      },
      dismiss: () => undefined,
    };
  }
  return ctx;
}
