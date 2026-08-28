"use client";

import { Button, Card, EmptyState } from "@/components/ui";
import { theme } from "@/lib/theme";

const tracks = [
  { id: "original", label: "Original (ZH)", color: theme.speaker1 },
  { id: "voice_vi", label: "Voice (VI)", color: theme.speaker2 },
  { id: "music", label: "Music", color: theme.speaker3 },
  { id: "sfx", label: "SFX", color: theme.speaker4 },
];

export function AudioPanel() {
  return (
    <Card padded={false}>
      <div
        style={{
          padding: "10px 12px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          background: "#0d172e",
        }}
      >
        <strong style={{ fontSize: 13 }}>Audio Mix</strong>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <Button>Auto-level</Button>
          <Button variant="primary">Render mix</Button>
        </div>
      </div>
      {tracks.map((t) => (
        <div
          key={t.id}
          style={{
            padding: "12px",
            borderBottom: `1px solid ${theme.border}`,
            display: "grid",
            gridTemplateColumns: "120px 60px 1fr 60px",
            gap: 12,
            alignItems: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: 999, background: t.color }} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>{t.label}</span>
          </div>
          <div style={{ display: "flex", gap: 4 }}>
            <Button size="sm">M</Button>
            <Button size="sm">S</Button>
          </div>
          <input type="range" min={0} max={1.5} step={0.01} defaultValue={1} style={{ width: "100%" }} />
          <span style={{ fontSize: 11, color: theme.textMuted, textAlign: "right" }}>0 dB</span>
        </div>
      ))}
    </Card>
  );
}
