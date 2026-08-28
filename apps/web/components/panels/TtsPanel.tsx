"use client";

import { api } from "@/lib/api";
import { Button, Card, EmptyState, Select, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";

export function TtsPanel() {
  const translation = useEditor((s) => s.translation);
  const voices = useEditor((s) => s.voices);
  const speakers = useEditor((s) => s.speakers);
  const setTime = useEditor((s) => s.setTime);
  const projectId = useEditor((s) => s.projectId);

  if (translation.length === 0) {
    return (
      <EmptyState
        title="Chưa có segment để tổng hợp"
        description="Hoàn thành bước Translation trước."
      />
    );
  }

  return (
    <Card padded={false}>
      <div
        style={{
          padding: "10px 12px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "#0d172e",
        }}
      >
        <strong style={{ fontSize: 13 }}>TTS Generation</strong>
        <span style={{ fontSize: 11, color: theme.textMuted }}>{translation.length} segments</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <Button>Generate Selected</Button>
          <Button variant="primary">Generate All</Button>
        </div>
      </div>
      {translation.map((t) => {
        const speaker = speakers.find((s) => s.id === t.speaker_id);
        const voice = voices.find((v) => v.id === speaker?.voice_profile_id);
        return (
          <div
            key={t.id}
            style={{
              padding: "10px 12px",
              borderBottom: `1px solid ${theme.border}`,
              display: "grid",
              gridTemplateColumns: "70px 1fr 200px 120px 110px",
              gap: 10,
              alignItems: "center",
              fontSize: 12,
            }}
          >
            <span style={{ fontVariantNumeric: "tabular-nums", color: theme.textMuted }}>
              {fmt(t.start_ms)}
            </span>
            <span
              onClick={() => setTime(t.start_ms)}
              style={{ cursor: "pointer" }}
            >
              {t.text}
            </span>
            <Select defaultValue={voice?.id ?? ""}>
              <option value="">— Voice —</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </Select>
            <span>
              <StatusDot status="completed" /> Generated
            </span>
            <div style={{ display: "flex", gap: 4 }}>
              <Button size="sm">▶</Button>
              <Button size="sm">↻</Button>
            </div>
          </div>
        );
      })}
    </Card>
  );
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
