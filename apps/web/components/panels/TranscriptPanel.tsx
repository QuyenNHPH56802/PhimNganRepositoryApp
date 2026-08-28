"use client";

import { useMemo } from "react";
import { useEditor } from "@/lib/store";
import { Button, Card, EmptyState, Input, StatusDot } from "@/components/ui";
import { speakerColor, theme } from "@/lib/theme";
import type { TranscriptSegment } from "@/lib/types";

export function TranscriptPanel() {
  const transcript = useEditor((s) => s.transcript);
  const setTime = useEditor((s) => s.setTime);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);

  const grouped = useMemo(() => groupBySpeaker(transcript), [transcript]);

  if (transcript.length === 0) {
    return (
      <EmptyState
        title="Chưa có transcript"
        description="Chạy bước ASR để tạo transcript từ audio gốc."
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", gap: 8 }}>
        <Input placeholder="Tìm theo Chinese / speaker / timestamp" />
        <Button>Tìm</Button>
      </div>
      {grouped.map((g) => (
        <Card key={g.speakerId} padded={false}>
          <div
            style={{
              padding: "8px 12px",
              borderBottom: `1px solid ${theme.border}`,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: 10,
                height: 10,
                borderRadius: 999,
                background: speakerColor(g.speakerIndex),
              }}
            />
            <strong style={{ fontSize: 12 }}>{g.speakerLabel}</strong>
            <span style={{ fontSize: 11, color: theme.textMuted }}>{g.segments.length} segments</span>
          </div>
          {g.segments.map((seg) => {
            const active = currentTimeMs >= seg.start_ms && currentTimeMs < seg.end_ms;
            return (
              <div
                key={seg.id}
                onClick={() => setTime(seg.start_ms)}
                style={{
                  padding: "10px 12px",
                  borderBottom: `1px solid ${theme.border}`,
                  cursor: "pointer",
                  display: "grid",
                  gridTemplateColumns: "80px 1fr 80px",
                  gap: 12,
                  alignItems: "center",
                  background: active ? "rgba(125,211,252,0.06)" : "transparent",
                }}
              >
                <span style={{ fontSize: 11, color: theme.textMuted, fontVariantNumeric: "tabular-nums" }}>
                  {fmt(seg.start_ms)}
                </span>
                <span style={{ fontSize: 13 }}>{seg.text}</span>
                <span style={{ fontSize: 10, color: theme.textDim, textAlign: "right" }}>
                  conf {((seg.confidence ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </Card>
      ))}
    </div>
  );
}

function groupBySpeaker(segments: TranscriptSegment[]) {
  const groups: Record<string, TranscriptSegment[]> = {};
  segments.forEach((s) => {
    const key = s.speaker_id ?? "unknown";
    groups[key] ??= [];
    groups[key].push(s);
  });
  return Object.entries(groups).map(([speakerId, segs], i) => ({
    speakerId,
    speakerIndex: i,
    speakerLabel: segs[0]?.speaker_id ? `Speaker ${i + 1}` : "Unknown",
    segments: segs,
  }));
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  const t = Math.floor(ms % 1000 / 100);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${t}`;
}
