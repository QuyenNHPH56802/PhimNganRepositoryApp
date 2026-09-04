"use client";

import { useEffect, useState } from "react";
import { theme } from "@/lib/theme";

/**
 * Environment indicator badge.
 *
 * Visible only outside production. Shows current env name + git SHA so developers
 * can confirm at a glance which build is loaded. Tries `/api/version` first;
 * falls back to `NEXT_PUBLIC_APP_ENV` (build-time) if the API is unreachable.
 *
 * Note: only renders on the client to avoid hydration mismatches.
 */
export function EnvBadge() {
  const [meta, setMeta] = useState<{ env: string; sha: string; build: string } | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    // Don't probe in production — the badge stays hidden.
    if (process.env.NODE_ENV === "production") return;

    let cancelled = false;
    fetch("/api/healthz", { method: "GET" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        // Expect shape { env, sha, build } or similar — only set what we have.
        setMeta({
          env: data?.env ?? process.env.NEXT_PUBLIC_APP_ENV ?? "development",
          sha: data?.sha ?? "",
          build: data?.build ?? "",
        });
      })
      .catch(() => {
        if (cancelled) return;
        setMeta({
          env: process.env.NEXT_PUBLIC_APP_ENV ?? "development",
          sha: "",
          build: "",
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (typeof window === "undefined") return null;
  if (process.env.NODE_ENV === "production") return null;
  if (!meta) return null;

  const shortSha = meta.sha ? meta.sha.slice(0, 7) : "local";

  return (
    <span
      title={
        meta.sha
          ? `Build ${meta.build} · Commit ${meta.sha}`
          : `Build ${meta.build || "dev"}`
      }
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 8px",
        borderRadius: 4,
        background: meta.env === "staging" ? "rgba(251,191,36,0.15)" : "rgba(125,211,252,0.12)",
        color: meta.env === "staging" ? "#f59e0b" : theme.accent,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 0.3,
        border: `1px solid ${meta.env === "staging" ? "rgba(251,191,36,0.3)" : "rgba(125,211,252,0.3)"}`,
        fontFamily: "ui-monospace, monospace",
        textTransform: "uppercase",
        lineHeight: 1.5,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: 999,
          background: meta.env === "staging" ? "#f59e0b" : theme.accent,
          boxShadow: `0 0 4px ${meta.env === "staging" ? "#f59e0b" : theme.accent}`,
        }}
      />
      {meta.env} · {shortSha}
    </span>
  );
}
