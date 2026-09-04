"use client";

import { useState } from "react";

const MODES = [
  { id: "fast", label: "FAST", cps: 18, voiceClone: false },
  { id: "balanced", label: "BALANCED", cps: 16, voiceClone: false },
  { id: "high", label: "HIGH", cps: 14, voiceClone: true },
] as const;

export default function QualityModePage({ params }: { params: { id: string } }) {
  const [mode, setMode] = useState<typeof MODES[number]["id"]>("balanced");
  const [policy, setPolicy] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function apply(next: typeof mode) {
    setError(null);
    setLoading(true);
    try {
      // Use the Next.js proxy route so the request always includes the
      // right Authorization/Cookie headers and gets a proper error code.
      const response = await fetch(`/api/projects/${params.id}/quality-mode`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: next }),
      });
      if (!response.ok) {
        setError(`HTTP ${response.status}: ${await response.text()}`);
        return;
      }
      const body = await response.json();
      setMode(next);
      setPolicy(body.policy ?? body);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 720, display: "flex", flexDirection: "column", gap: 16 }}>
      <h1 style={{ fontSize: 22, margin: 0 }}>Quality mode</h1>
      <p style={{ margin: 0, color: "#94a3b8", fontSize: 13 }}>
        Chọn chế độ chất lượng cho dự án. Áp dụng cho lần chạy workflow tiếp theo.
      </p>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => apply(m.id)}
            disabled={loading}
            style={{
              flex: 1,
              minWidth: 160,
              border: `2px solid ${mode === m.id ? "#0ea5e9" : "#1f2a44"}`,
              background: mode === m.id ? "rgba(14,165,233,0.10)" : "#111c33",
              color: mode === m.id ? "#7dd3fc" : "#e2e8f0",
              padding: "12px 16px",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 700,
              cursor: loading ? "wait" : "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >
            <div>{m.label}</div>
            <div style={{ fontSize: 11, fontWeight: 400, marginTop: 4, opacity: 0.8 }}>
              {m.cps} cps{!m.voiceClone ? "" : " • voice clone"}
            </div>
          </button>
        ))}
      </div>
      {error && (
        <div
          role="alert"
          style={{
            background: "#450a0a",
            color: "#ef4444",
            padding: 12,
            borderRadius: 6,
            fontSize: 13,
            border: "1px solid #7f1d1d",
          }}
        >
          ❌ {error}
        </div>
      )}
      {policy && (
        <pre
          style={{
            background: "#111c33",
            color: "#7dd3fc",
            padding: 16,
            borderRadius: 8,
            fontSize: 12,
            overflow: "auto",
            border: "1px solid #1f2a44",
          }}
        >
          {JSON.stringify(policy, null, 2)}
        </pre>
      )}
    </div>
  );
}