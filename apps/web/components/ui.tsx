"use client";

import clsx from "clsx";
import { theme } from "@/lib/theme";

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
}: {
  children: React.ReactNode;
  variant?: "default" | "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  type?: "button" | "submit";
  title?: string;
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
  return (
    <button
      type={type ?? "button"}
      title={title}
      disabled={disabled}
      onClick={onClick}
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
