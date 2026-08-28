"use client";

import { useState } from "react";
import { useEditor } from "@/lib/store";
import { Badge, Button, Card, EmptyState, StatusDot } from "@/components/ui";
import { speakerColor, theme } from "@/lib/theme";
import type { TranslationSegment } from "@/lib/types";

const STATUS_TONE: Record<TranslationSegment["status"], "neutral" | "info" | "success" | "warn" | "danger"> = {
  auto: "neutral",
  review: "warn",
  edited: "info",
  approved: "success",
  error: "danger",
};

export function TranslationPanel() {
  const translation = useEditor((s) => s.translation);
  const transcript = useEditor((s) => s.transcript);
  const updateTranslationSegment = useEditor((s) => s.updateTranslationSegment);
  const setTime = useEditor((s) => s.setTime);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const [filter, setFilter] = useState<"all" | TranslationSegment["status"]>("all");

  const rows = translation
    .map((t) => {
      const source = transcript.find((x) => x.id === t.transcript_segment_id);
      return { translation: t, source };
    })
    .filter((r) => (filter === "all" ? true : r.translation.status === filter));

  if (translation.length === 0) {
    return (
      <EmptyState
        title="Chưa có bản dịch"
        description="Chạy bước Translation để tạo bản dịch Tiếng Việt."
        action={<Button variant="primary">Dịch ngay</Button>}
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {(["all", "auto", "review", "edited", "approved", "error"] as const).map((s) => (
          <Button
            key={s}
            size="sm"
            variant={filter === s ? "primary" : "default"}
            onClick={() => setFilter(s)}
          >
            {s}
          </Button>
        ))}
      </div>
      {rows.map(({ translation: t, source }) => {
        const speakerIndex = Number(t.speaker_id?.slice(-1) ?? "0") || 0;
        const active = currentTimeMs >= t.start_ms && currentTimeMs < t.end_ms;
        return (
          <Card key={t.id} padded={false}>
            <div
              onClick={() => setTime(t.start_ms)}
              style={{
                padding: "10px 12px",
                borderBottom: `1px solid ${theme.border}`,
                display: "flex",
                gap: 8,
                alignItems: "center",
                cursor: "pointer",
                background: active ? "rgba(125,211,252,0.06)" : "transparent",
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 999,
                  background: speakerColor(speakerIndex),
                }}
              />
              <span style={{ fontSize: 11, color: theme.textMuted, fontVariantNumeric: "tabular-nums" }}>
                {fmt(t.start_ms)}–{fmt(t.end_ms)}
              </span>
              <Badge tone={STATUS_TONE[t.status]}>{t.status}</Badge>
              <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                <Button size="sm" variant="ghost">Accept</Button>
                <Button size="sm" variant="ghost">Regenerate</Button>
              </div>
            </div>
            <div style={{ padding: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, color: theme.textMuted, marginBottom: 4 }}>ZH (source)</div>
                <div style={{ fontSize: 13 }}>{source?.text ?? "—"}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: theme.textMuted, marginBottom: 4 }}>VI (translation)</div>
                <textarea
                  value={t.text}
                  onChange={(e) => updateTranslationSegment(t.id, e.target.value)}
                  rows={2}
                  style={{
                    width: "100%",
                    background: theme.bgElevated,
                    border: `1px solid ${theme.border}`,
                    color: theme.text,
                    padding: 8,
                    borderRadius: 6,
                    fontSize: 13,
                    fontFamily: "inherit",
                    resize: "vertical",
                  }}
                />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
