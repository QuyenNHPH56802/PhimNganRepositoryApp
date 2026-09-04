"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEditor } from "@/lib/store";
import { Badge, Button, Card, EmptyState, Modal } from "@/components/ui";
import { speakerColor, theme } from "@/lib/theme";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { humanizeError } from "@/lib/errorMessage";
import type { TranslationSegment } from "@/lib/types";

const STATUS_LABELS: Record<TranslationSegment["status"], string> = {
  auto: "Tự động",
  review: "Cần duyệt",
  edited: "Đã sửa",
  approved: "Đã duyệt",
  error: "Lỗi",
};

const STATUS_TONE: Record<TranslationSegment["status"], "neutral" | "info" | "success" | "warn" | "danger"> = {
  auto: "neutral",
  review: "warn",
  edited: "info",
  approved: "success",
  error: "danger",
};

const FILTER_OPTIONS: { key: "all" | TranslationSegment["status"]; label: string }[] = [
  { key: "all", label: "Tất cả" },
  { key: "auto", label: "Tự động" },
  { key: "review", label: "Cần duyệt" },
  { key: "edited", label: "Đã sửa" },
  { key: "approved", label: "Đã duyệt" },
  { key: "error", label: "Lỗi" },
];

export function TranslationPanel() {
  const router = useRouter();
  const translation = useEditor((s) => s.translation);
  const transcript = useEditor((s) => s.transcript);
  const updateTranslationSegment = useEditor((s) => s.updateTranslationSegment);
  const setTime = useEditor((s) => s.setTime);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const projectId = useEditor((s) => s.projectId);
  const [filter, setFilter] = useState<"all" | TranslationSegment["status"]>("all");
  const [regenerating, setRegenerating] = useState<string | null>(null);
  const [pendingRegenerate, setPendingRegenerate] = useState<TranslationSegment | null>(null);
  const { toast } = useToast();

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
        description="Chạy bước Translation từ trang Project để tạo bản dịch Tiếng Việt."
        action={
          <Button variant="primary" onClick={() => projectId && router.push(`/projects/${projectId}`)}>
            Mở trang Project
          </Button>
        }
      />
    );
  }

  async function onRegenerate(segmentId: string) {
    if (!projectId) return;
    setRegenerating(segmentId);
    try {
      const result = await api.regenerateTranslation(projectId, segmentId);
      if (result) {
        updateTranslationSegment(segmentId, result.display_text, "auto");
        toast("Đã tạo lại bản dịch", "success");
      } else {
        toast("Không nhận được bản dịch mới từ provider", "warn");
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo lại bản dịch").title, "danger");
    } finally {
      setRegenerating(null);
    }
  }

  function handleRegenerateClick(t: TranslationSegment) {
    // Approved segments get a confirm modal — overwriting an approved
    // translation is destructive.
    if (t.status === "approved") {
      setPendingRegenerate(t);
      return;
    }
    onRegenerate(t.id);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {FILTER_OPTIONS.map((opt) => (
          <Button
            key={opt.key}
            size="sm"
            variant={filter === opt.key ? "primary" : "default"}
            onClick={() => setFilter(opt.key)}
          >
            {opt.label}
          </Button>
        ))}
      </div>
      {rows.length === 0 && (
        <div
          style={{
            padding: 16,
            color: theme.textMuted,
            fontSize: 13,
            textAlign: "center",
            background: theme.bgElevated,
            border: `1px solid ${theme.border}`,
            borderRadius: 8,
          }}
        >
          Không có segment khớp với bộ lọc này.
          <div style={{ marginTop: 8 }}>
            <Button size="sm" variant="ghost" onClick={() => setFilter("all")}>
              ✕ Bỏ lọc
            </Button>
          </div>
        </div>
      )}
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
              <Badge tone={STATUS_TONE[t.status]}>{STATUS_LABELS[t.status]}</Badge>
              <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={t.status === "approved"}
                  onClick={() => updateTranslationSegment(t.id, undefined, "approved")}
                >
                  ✓ Duyệt
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={regenerating === t.id}
                  onClick={(e) => { e.stopPropagation(); handleRegenerateClick(t); }}
                >
                  {regenerating === t.id ? "..." : "↻ Tạo lại"}
                </Button>
              </div>
            </div>
            <div style={{ padding: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <div style={{ fontSize: 10, color: theme.textMuted, marginBottom: 4 }}>ZH (nguồn)</div>
                <div style={{ fontSize: 13 }}>{source?.normalized_text || source?.raw_text || source?.text || "—"}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: theme.textMuted, marginBottom: 4 }}>VI (bản dịch)</div>
                <textarea
                  value={t.display_text || t.tts_text || t.text || ""}
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
      <Modal
        open={!!pendingRegenerate}
        onClose={() => setPendingRegenerate(null)}
        title="Bản dịch đã được duyệt"
      >
        {pendingRegenerate && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: 0, fontSize: 13, color: theme.text }}>
              Bản dịch này đang ở trạng thái <strong>Đã duyệt</strong>. Tạo lại sẽ thay thế nội dung và chuyển
              về trạng thái <strong>Tự động</strong>. Tiếp tục?
            </p>
            <p style={{ margin: 0, fontSize: 12, color: theme.textMuted, background: theme.bgPanel, padding: 8, borderRadius: 6 }}>
              Bản dịch hiện tại: <em>"{pendingRegenerate.display_text || pendingRegenerate.tts_text || pendingRegenerate.text || "—"}"</em>
            </p>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <Button onClick={() => setPendingRegenerate(null)}>Huỷ</Button>
              <Button
                variant="primary"
                onClick={() => {
                  const seg = pendingRegenerate;
                  setPendingRegenerate(null);
                  onRegenerate(seg.id);
                }}
              >
                ↻ Tạo lại
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
