"use client";

import { useState, useEffect, useRef } from "react";
import { useEditor } from "@/lib/store";
import { Button, Card, EmptyState, Modal, Textarea } from "@/components/ui";
import { theme } from "@/lib/theme";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { humanizeError } from "@/lib/errorMessage";

export function SubtitlePanel() {
  const subtitles = useEditor((s) => s.subtitles);
  const updateSubtitleSegment = useEditor((s) => s.updateSubtitleSegment);
  const splitSubtitle = useEditor((s) => s.splitSubtitle);
  const mergeSubtitleWith = useEditor((s) => s.mergeSubtitleWith);
  const deleteSubtitle = useEditor((s) => s.deleteSubtitle);
  const loadSubtitles = useEditor((s) => s.loadSubtitles);
  const selectedSegmentId = useEditor((s) => s.selectedSegmentId);
  const selectSegment = useEditor((s) => s.selectSegment);
  const setTime = useEditor((s) => s.setTime);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const projectId = useEditor((s) => s.projectId);
  const toast = useToast();

  const [inspectorText, setInspectorText] = useState("");
  const [generating, setGenerating] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const isTypingRef = useRef(false);

  async function handleGenerateSubtitles() {
    if (!projectId || generating) return;
    setGenerating(true);
    try {
      const result = await api.generateSubtitles(projectId);
      if (result?.segments) {
        loadSubtitles(result.segments);
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo phụ đề").title, "danger");
    } finally {
      setGenerating(false);
    }
  }

  if (subtitles.length === 0) {
    return (
      <EmptyState
        title="Chưa có subtitle"
        description="Chạy bước Subtitle từ trang Project để tạo subtitle VI từ translation."
        action={
          <Button variant="primary" disabled={generating} onClick={() => void handleGenerateSubtitles()}>
            {generating ? "⏳ Đang tạo…" : "Tạo subtitle"}
          </Button>
        }
      />
    );
  }

  const selectedIdx = subtitles.findIndex((s) => s.id === selectedSegmentId);
  const selected = selectedIdx >= 0 ? subtitles[selectedIdx] : null;

  // Sync inspector text with selected segment, but only when the user is not
  // actively editing the textarea. Without this guard the store round-trip
  // (onChange → setText → re-render) would clobber in-progress typing.
  useEffect(() => {
    if (selected && !isTypingRef.current) {
      const next = selected.text || "";
      if (next !== inspectorText) setInspectorText(next);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id, selected?.text]);

  function handleSplitAtPlayhead() {
    if (!selectedSegmentId) return;
    // Find if playhead is within selected segment
    const seg = subtitles.find((s) => s.id === selectedSegmentId);
    if (!seg) return;
    
    if (currentTimeMs > seg.start_ms && currentTimeMs < seg.end_ms) {
      splitSubtitle(selectedSegmentId, currentTimeMs);
    } else {
      // Split at middle of segment
      const midMs = Math.floor((seg.start_ms + seg.end_ms) / 2);
      splitSubtitle(selectedSegmentId, midMs);
    }
  }

  function handleMergeWithNext() {
    if (!selectedSegmentId || selectedIdx < 0) return;
    const next = subtitles[selectedIdx + 1];
    if (next) {
      mergeSubtitleWith(selectedSegmentId, next.id);
    }
  }

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
          <span style={{ fontSize: 11, color: theme.textDim, marginLeft: "auto" }}>
            Click để chọn • Double-click để chia segment
          </span>
        </div>
        <div style={{ maxHeight: 480, overflowY: "auto" }}>
          {subtitles.map((seg, idx) => {
            const isActive = currentTimeMs >= seg.start_ms && currentTimeMs < seg.end_ms;
            return (
              <div
                key={seg.id}
                onClick={() => selectSegment(seg.id)}
                style={{
                  padding: "8px 12px",
                  borderBottom: `1px solid ${theme.border}`,
                  display: "grid",
                  gridTemplateColumns: "110px 1fr 100px",
                  gap: 8,
                  alignItems: "center",
                  background: seg.id === selectedSegmentId 
                    ? "rgba(125,211,252,0.12)" 
                    : isActive 
                      ? "rgba(125,211,252,0.06)"
                      : "transparent",
                  cursor: "pointer",
                }}
              >
                <span 
                  style={{ 
                    fontSize: 11, 
                    color: isActive ? theme.accent : theme.textMuted, 
                    fontVariantNumeric: "tabular-nums",
                    cursor: "pointer"
                  }}
                  onClick={(e) => { e.stopPropagation(); setTime(seg.start_ms); }}
                >
                  {fmt(seg.start_ms)} → {fmt(seg.end_ms)}
                </span>
                <span 
                  style={{ fontSize: 13 }}
                  onDoubleClick={(e) => {
                    e.stopPropagation();
                    // Split at middle
                    const midMs = Math.floor((seg.start_ms + seg.end_ms) / 2);
                    splitSubtitle(seg.id, midMs);
                  }}
                >
                  {seg.text || seg.display_text || ""}
                </span>
                <div style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      const midMs = Math.floor((seg.start_ms + seg.end_ms) / 2);
                      splitSubtitle(seg.id, midMs); 
                    }}
                    title="Chia segment"
                  >
                    Chia
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={(e) => { e.stopPropagation(); setPendingDeleteId(seg.id); }}
                    title="Xóa segment"
                  >
                    ×
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Inspector">
        {selected ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <Field label="Thời điểm bắt đầu (ms)">
              <input
                type="number"
                value={selected.start_ms}
                onChange={(e) => updateSubtitleSegment(selected.id, { start_ms: parseInt(e.target.value, 10) || 0 })}
                style={inputStyle}
              />
            </Field>
            <Field label="Thời điểm kết thúc (ms)">
              <input
                type="number"
                value={selected.end_ms}
                onChange={(e) => updateSubtitleSegment(selected.id, { end_ms: parseInt(e.target.value, 10) || 0 })}
                style={inputStyle}
              />
            </Field>
            <Field label="Nội dung phụ đề">
              <Textarea
                value={inspectorText}
                onFocus={() => {
                  isTypingRef.current = true;
                }}
                onBlur={() => {
                  isTypingRef.current = false;
                }}
                onChange={(e) => {
                  setInspectorText(e.target.value);
                  updateSubtitleSegment(selected.id, { text: e.target.value });
                }}
                rows={4}
              />
            </Field>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Button 
                size="sm" 
                onClick={handleSplitAtPlayhead}
                title={`Chia tại vị trí ${fmt(currentTimeMs)}`}
              >
                ✂ Chia tại playhead ({fmt(currentTimeMs)})
              </Button>
              <Button 
                size="sm" 
                variant="ghost"
                disabled={selectedIdx >= subtitles.length - 1}
                onClick={handleMergeWithNext}
              >
                ⟿ Gộp với tiếp {selectedIdx < subtitles.length - 1 ? `"${subtitles[selectedIdx + 1]?.text?.slice(0, 20)}..."` : ""}
              </Button>
            </div>
            
            <div style={{ fontSize: 11, color: theme.textDim, marginTop: 8 }}>
              Segment {selectedIdx + 1} / {subtitles.length}
            </div>
          </div>
        ) : (
          <div style={{ color: theme.textMuted, fontSize: 12 }}>
            Chọn một segment để chỉnh sửa.
          </div>
        )}
      </Card>
      <Modal
        open={!!pendingDeleteId}
        onClose={() => setPendingDeleteId(null)}
        title="Xóa subtitle segment?"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <p style={{ margin: 0, fontSize: 13 }}>
            Bạn có chắc chắn muốn xóa segment này? Hành động không thể hoàn tác (nhưng có thể Undo bằng Ctrl+Z).
          </p>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <Button onClick={() => setPendingDeleteId(null)}>Huỷ</Button>
            <Button
              variant="danger"
              onClick={() => {
                if (pendingDeleteId) deleteSubtitle(pendingDeleteId);
                setPendingDeleteId(null);
              }}
            >
              🗑 Xóa
            </Button>
          </div>
        </div>
      </Modal>
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
