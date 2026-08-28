"use client";

import { useEditor } from "@/lib/store";
import { Button, Card, EmptyState, Textarea } from "@/components/ui";
import { theme } from "@/lib/theme";

export function SubtitlePanel() {
  const subtitles = useEditor((s) => s.subtitles);
  const updateSubtitleSegment = useEditor((s) => s.updateSubtitleSegment);
  const splitSubtitle = useEditor((s) => s.splitSubtitle);
  const mergeSubtitleWith = useEditor((s) => s.mergeSubtitleWith);
  const deleteSubtitle = useEditor((s) => s.deleteSubtitle);
  const selectedSegmentId = useEditor((s) => s.selectedSegmentId);
  const setTime = useEditor((s) => s.setTime);

  if (subtitles.length === 0) {
    return (
      <EmptyState
        title="Chưa có subtitle"
        description="Chạy bước Subtitle để tạo subtitle VI từ translation."
        action={<Button variant="primary">Tạo subtitle</Button>}
      />
    );
  }

  const selectedIdx = subtitles.findIndex((s) => s.id === selectedSegmentId);
  const selected = selectedIdx >= 0 ? subtitles[selectedIdx] : null;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 12 }}>
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
          <strong style={{ fontSize: 13 }}>Subtitle segments</strong>
          <span style={{ fontSize: 11, color: theme.textMuted }}>{subtitles.length}</span>
        </div>
        <div style={{ maxHeight: 480, overflowY: "auto" }}>
          {subtitles.map((seg) => (
            <div
              key={seg.id}
              onClick={() => setTime(seg.start_ms)}
              style={{
                padding: "8px 12px",
                borderBottom: `1px solid ${theme.border}`,
                display: "grid",
                gridTemplateColumns: "110px 1fr 100px",
                gap: 8,
                alignItems: "center",
                background: seg.id === selectedSegmentId ? "rgba(125,211,252,0.08)" : "transparent",
                cursor: "pointer",
              }}
            >
              <span style={{ fontSize: 11, color: theme.textMuted, fontVariantNumeric: "tabular-nums" }}>
                {fmt(seg.start_ms)} → {fmt(seg.end_ms)}
              </span>
              <span style={{ fontSize: 13 }}>{seg.text}</span>
              <div style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                <Button size="sm" onClick={(e) => { e.stopPropagation(); splitSubtitle(seg.id, (seg.start_ms + seg.end_ms) / 2); }}>Split</Button>
                <Button size="sm" variant="danger" onClick={(e) => { e.stopPropagation(); deleteSubtitle(seg.id); }}>×</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Inspector">
        {selected ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Field label="Start (ms)">
              <input
                type="number"
                value={selected.start_ms}
                onChange={(e) => updateSubtitleSegment(selected.id, { start_ms: parseInt(e.target.value, 10) || 0 })}
                style={inputStyle}
              />
            </Field>
            <Field label="End (ms)">
              <input
                type="number"
                value={selected.end_ms}
                onChange={(e) => updateSubtitleSegment(selected.id, { end_ms: parseInt(e.target.value, 10) || 0 })}
                style={inputStyle}
              />
            </Field>
            <Field label="Text">
              <Textarea
                value={selected.text}
                onChange={(e) => updateSubtitleSegment(selected.id, { text: e.target.value })}
                rows={4}
              />
            </Field>
            <div style={{ display: "flex", gap: 6 }}>
              <Button size="sm">Split at playhead</Button>
              <Button
                size="sm"
                disabled={selectedIdx >= subtitles.length - 1}
                onClick={() => {
                  const next = subtitles[selectedIdx + 1];
                  if (next) mergeSubtitleWith(selected.id, next.id);
                }}
              >
                Merge next
              </Button>
            </div>
          </div>
        ) : (
          <div style={{ color: theme.textMuted, fontSize: 12 }}>Chọn một segment để chỉnh.</div>
        )}
      </Card>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: theme.bgElevated,
  border: `1px solid ${theme.border}`,
  color: theme.text,
  padding: "6px 10px",
  borderRadius: 6,
  fontSize: 13,
  outline: "none",
  width: "100%",
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  const t = Math.floor(ms % 1000 / 100);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${t}`;
}
