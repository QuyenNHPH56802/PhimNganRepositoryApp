"use client";

import React from "react";
import clsx from "clsx";
import { theme } from "@/lib/theme";

/**
 * Skeleton — a placeholder with a shimmer animation shown while data is loading.
 *
 * Renders a rounded rectangle with a CSS gradient animation that sweeps left→right,
 * giving the visual impression of content being loaded.
 */
export function Skeleton({
  width,
  height = 14,
  style,
  className,
}: {
  width?: string | number;
  height?: string | number;
  style?: React.CSSProperties;
  className?: string;
}) {
  return (
    <span
      className={clsx("skeleton-shimmer", className)}
      style={{
        display: "inline-block",
        width: width ?? "100%",
        height,
        borderRadius: 4,
        background: theme.bgElevated,
        verticalAlign: "middle",
        ...style,
      }}
      aria-hidden="true"
    />
  );
}

/** Row of skeletons that approximates a typical list item. */
export function SkeletonRow({
  avatar = true,
  lines = 2,
  avatarColor,
}: {
  avatar?: boolean;
  lines?: number;
  avatarColor?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "10px 12px",
        borderBottom: `1px solid ${theme.border}`,
        alignItems: "flex-start",
      }}
    >
      {avatar && (
        <Skeleton
          width={32}
          height={32}
          style={{ borderRadius: "50%", flexShrink: 0, background: avatarColor ?? theme.speaker1 + "40" }}
        />
      )}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} width={i === lines - 1 ? "60%" : "100%"} height={12} />
        ))}
      </div>
    </div>
  );
}

/** Full panel loading skeleton with header + multiple skeleton rows. */
export function SkeletonPanel({
  title,
  rows = 5,
}: {
  title?: string;
  rows?: number;
}) {
  return (
    <div>
      {title && (
        <div
          style={{
            padding: "8px 12px",
            borderBottom: `1px solid ${theme.border}`,
            background: "#0d172e",
          }}
        >
          <Skeleton width={120} height={13} />
        </div>
      )}
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonRow key={i} avatar={i < 3} avatarColor={Object.values(theme).find((v) => typeof v === "string" && v.startsWith("#") && [theme.speaker1, theme.speaker2, theme.speaker3, theme.speaker4].includes(v)) as string} />
      ))}
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "success" | "warn" | "danger" | "info";
  children: React.ReactNode;
}) {
  const tones: Record<string, { bg: string; fg: string; border: string }> = {
    neutral: { bg: "#1e293b", fg: theme.textMuted, border: theme.border },
    success: { bg: "#052e16", fg: theme.success, border: "#14532d" },
    warn: { bg: "#422006", fg: theme.warn, border: "#713f12" },
    danger: { bg: "#450a0a", fg: theme.danger, border: "#7f1d1d" },
    info: { bg: "#0c4a6e", fg: theme.accent, border: "#0369a1" },
  };
  const t: { bg: string; fg: string; border: string } = tones[tone] ?? tones.neutral!;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        background: t.bg,
        color: t.fg,
        border: `1px solid ${t.border}`,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: 0.2,
      }}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = "default",
  size = "md",
  onClick,
  disabled,
  type,
  title,
  style,
  "aria-label": ariaLabel,
}: {
  children: React.ReactNode;
  variant?: "default" | "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  type?: "button" | "submit";
  title?: string;
  style?: React.CSSProperties;
  "aria-label"?: string;
}) {
  const sizes: Record<string, { padding: string; fontSize: number }> = {
    sm: { padding: "4px 10px", fontSize: 12 },
    md: { padding: "6px 14px", fontSize: 13 },
    lg: { padding: "8px 18px", fontSize: 14 },
    icon: { padding: "6px 8px", fontSize: 13 },
  };
  const variants: Record<string, { bg: string; fg: string; border: string; hoverBg: string }> = {
    default: { bg: theme.bgPanel, fg: theme.text, border: theme.border, hoverBg: "#16223e" },
    primary: { bg: theme.accentStrong, fg: "#0b1220", border: theme.accentStrong, hoverBg: "#38bdf8" },
    ghost: { bg: "transparent", fg: theme.text, border: "transparent", hoverBg: "#16223e" },
    danger: { bg: "#7f1d1d", fg: "#fee2e2", border: "#7f1d1d", hoverBg: "#991b1b" },
  };
  const v: { bg: string; fg: string; border: string; hoverBg: string } = variants[variant] ?? variants.default!;
  const sz: { padding: string; fontSize: number } = sizes[size] ?? sizes.md!;
  // For icon-only buttons, fall back to `title` so screen readers still get a label.
  const computedAriaLabel = ariaLabel ?? (size === "icon" ? title : undefined);
  return (
    <button
      type={type ?? "button"}
      title={title}
      disabled={disabled}
      onClick={onClick}
      aria-label={computedAriaLabel}
      className={clsx("translator-btn")}
      style={{
        background: v.bg,
        color: v.fg,
        border: `1px solid ${v.border}`,
        padding: sz.padding,
        fontSize: sz.fontSize,
        fontWeight: 600,
        borderRadius: 6,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "background 120ms ease",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled) (e.currentTarget as HTMLButtonElement).style.background = v.hoverBg;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.background = v.bg;
      }}
    >
      {children}
    </button>
  );
}

export function Card({
  children,
  title,
  action,
  padded = true,
}: {
  children: React.ReactNode;
  title?: string;
  action?: React.ReactNode;
  padded?: boolean;
}) {
  return (
    <div
      style={{
        background: theme.bgPanel,
        border: `1px solid ${theme.border}`,
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      {title && (
        <div
          style={{
            padding: "10px 14px",
            borderBottom: `1px solid ${theme.border}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "#0d172e",
          }}
        >
          <span style={{ fontWeight: 600, fontSize: 13, color: theme.text }}>{title}</span>
          {action}
        </div>
      )}
      <div style={{ padding: padded ? 14 : 0 }}>{children}</div>
    </div>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        background: theme.bgElevated,
        border: `1px solid ${theme.border}`,
        color: theme.text,
        padding: "6px 10px",
        borderRadius: 6,
        fontSize: 13,
        outline: "none",
        width: "100%",
        ...(props.style ?? {}),
      }}
    />
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      style={{
        background: theme.bgElevated,
        border: `1px solid ${theme.border}`,
        color: theme.text,
        padding: "8px 10px",
        borderRadius: 6,
        fontSize: 13,
        outline: "none",
        width: "100%",
        minHeight: 60,
        fontFamily: "inherit",
        resize: "vertical",
        ...(props.style ?? {}),
      }}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      style={{
        background: theme.bgElevated,
        border: `1px solid ${theme.border}`,
        color: theme.text,
        padding: "6px 10px",
        borderRadius: 6,
        fontSize: 13,
        outline: "none",
        width: "100%",
        ...(props.style ?? {}),
      }}
    />
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 24px",
        color: theme.textMuted,
        textAlign: "center",
        gap: 8,
      }}
    >
      {icon && <div style={{ fontSize: 32, opacity: 0.7 }}>{icon}</div>}
      <div style={{ fontSize: 15, fontWeight: 600, color: theme.text }}>{title}</div>
      {description && <div style={{ fontSize: 13, maxWidth: 360 }}>{description}</div>}
      {action && <div style={{ marginTop: 12 }}>{action}</div>}
    </div>
  );
}

export function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: theme.success,
    ready: theme.success,
    approved: theme.success,
    processing: theme.warn,
    running: theme.warn,
    pending: theme.textDim,
    draft: theme.textDim,
    failed: theme.danger,
    error: theme.danger,
    editing: theme.accent,
    review: theme.accent,
    translating: theme.accent,
  };
  const color = map[status.toLowerCase()] ?? theme.textDim;
  return (
    <span
      role="status"
      aria-label={`Trạng thái: ${status}`}
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: 999,
        background: color,
        boxShadow: `0 0 8px ${color}`,
        marginRight: 6,
      }}
    />
  );
}

export function Modal({
  open,
  onClose,
  title,
  children,
  width = 460,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  width?: number;
}) {
  // Lock body scroll and close on Escape for a11y parity with native dialogs.
  React.useEffect(() => {
    if (!open) return;
    const prevOverflow = document.documentElement.style.overflow;
    document.documentElement.classList.add("modal-open");
    document.documentElement.style.overflow = "hidden";
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.documentElement.classList.remove("modal-open");
      document.documentElement.style.overflow = prevOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(2,6,23,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: theme.bgPanel,
          border: `1px solid ${theme.border}`,
          borderRadius: 10,
          width,
          maxWidth: "calc(100vw - 32px)",
          maxHeight: "calc(100vh - 64px)",
          overflow: "auto",
          boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
        }}
      >
        <div
          style={{
            padding: "12px 16px",
            borderBottom: `1px solid ${theme.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "#0d172e",
          }}
        >
          <strong style={{ fontSize: 14 }}>{title}</strong>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: theme.textMuted,
              fontSize: 18,
              cursor: "pointer",
              lineHeight: 1,
            }}
            aria-label="Đóng"
          >
            ×
          </button>
        </div>
        <div style={{ padding: 16 }}>{children}</div>
      </div>
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
  onDismiss,
}: {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  return (
    <div
      role="alert"
      style={{
        background: "#450a0a",
        color: theme.danger,
        padding: 12,
        borderRadius: 8,
        fontSize: 13,
        border: "1px solid #7f1d1d",
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <span style={{ flex: 1 }}>❌ {message}</span>
      {onRetry && (
        <Button size="sm" variant="ghost" onClick={onRetry}>
          🔄 Thử lại
        </Button>
      )}
      {onDismiss && (
        <Button size="sm" variant="ghost" onClick={onDismiss} aria-label="Đóng thông báo lỗi">
          ✕
        </Button>
      )}
    </div>
  );
}

export function ProgressBar({
  value,
  hint,
  height = 6,
}: {
  value: number;
  hint?: string;
  height?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div>
      {hint && (
        <div style={{ fontSize: 11, color: theme.textMuted, marginBottom: 4 }}>{hint}</div>
      )}
      <div
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
        style={{
          height,
          background: theme.bgElevated,
          borderRadius: height / 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${clamped}%`,
            height: "100%",
            background: theme.accent,
            transition: "width 250ms ease",
          }}
        />
      </div>
    </div>
  );
}
