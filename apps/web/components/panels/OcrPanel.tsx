"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, SkeletonPanel, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  approveOcrRegion,
  deleteOcrRegion,
  listOcrRegions,
  patchOcrRegion,
  runOcr,
  type OcrRegion,
} from "@/lib/ocr";

interface Props {
  projectId: string;
}

const STATUSES = [
  { id: "all", label: "Tất cả" },
  { id: "pending", label: "Chờ dịch" },
  { id: "translated", label: "Đã dịch" },
  { id: "approved", label: "Đã duyệt" },
  { id: "rejected", label: "Bỏ qua" },
] as const;

export function OcrPanel({ projectId }: Props) {
  const { toast } = useToast();
  const [regions, setRegions] = useState<OcrRegion[] | null>(null);
  const [byStatus, setByStatus] = useState<Record<string, number>>({});
  const [filter, setFilter] = useState<typeof STATUSES[number]["id"]>("all");
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listOcrRegions(projectId, filter === "all" ? undefined : filter);
      setRegions(r.regions);
      setByStatus(r.by_status);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }, [projectId, filter, toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleRun() {
    setRunning(true);
    try {
      const result = await runOcr(projectId, { frame_count: 30, language_hint: "zh" });
      toast(
        `Đã quét ${result.frame_count} frames — tạo ${result.regions_created} regions (tổng: ${result.total_regions})`,
        "success",
      );
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setRunning(false);
    }
  }

  async function handleTranslate(r: OcrRegion, text: string) {
    try {
      const updated = await patchOcrRegion(projectId, r.id, {
        translated_text: text,
        status: text ? "translated" : r.status,
      });
      setRegions((prev) => prev?.map((x) => (x.id === updated.id ? updated : x)) ?? null);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleApprove(r: OcrRegion) {
    try {
      const updated = await approveOcrRegion(projectId, r.id);
      setRegions((prev) => prev?.map((x) => (x.id === updated.id ? updated : x)) ?? null);
      toast("Đã duyệt", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleDelete(r: OcrRegion) {
    if (!window.confirm("Xoá region này?")) return;
    try {
      await deleteOcrRegion(projectId, r.id);
      setRegions((prev) => prev?.filter((x) => x.id !== r.id) ?? null);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  if (loading && regions === null) {
    return <SkeletonPanel title="OCR — Text Detection" rows={4} />;
  }

  return (
    <Card
      title={
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          📷 OCR — Text Detection
          {Object.keys(byStatus).length > 0 && (
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 400 }}>
              ({Object.values(byStatus).reduce((a, b) => a + b, 0)} tổng)
            </span>
          )}
        </span>
      }
      action={
        <Button size="sm" variant="primary" onClick={handleRun} disabled={running}>
          {running ? "⏳ Đang quét…" : "🔍 Chạy OCR"}
        </Button>
      }
      padded={false}
    >
      {/* Status summary */}
      <div
        style={{
          display: "flex",
          gap: 8,
          padding: "10px 14px",
          borderBottom: `1px solid ${theme.border}`,
          background: "#0d172e",
          overflowX: "auto",
        }}
      >
        {STATUSES.map((s) => (
          <button
            key={s.id}
            onClick={() => setFilter(s.id)}
            style={{
              padding: "3px 10px",
              borderRadius: 4,
              border: `1px solid ${filter === s.id ? theme.accentStrong : theme.border}`,
              background: filter === s.id ? "rgba(125,211,252,0.1)" : "transparent",
              color: filter === s.id ? theme.text : theme.textMuted,
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {s.label} {s.id !== "all" && byStatus[s.id] ? `(${byStatus[s.id]})` : ""}
          </button>
        ))}
      </div>

      {!regions || regions.length === 0 ? (
        <EmptyState
          title="Chưa có region nào"
          description={
            filter === "all"
              ? "Nhấn Chạy OCR để phát hiện text trong video (mock provider dùng để demo)."
              : `Không có region ở trạng thái "${STATUSES.find((s) => s.id === filter)?.label}".`
          }
          action={
            filter === "all" && (
              <Button variant="primary" onClick={handleRun} disabled={running}>
                {running ? "…" : "Chạy OCR đầu tiên"}
              </Button>
            )
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column" }}>
          {regions.map((r) => (
            <RegionRow
              key={r.id}
              region={r}
              onTranslate={(t) => handleTranslate(r, t)}
              onApprove={() => handleApprove(r)}
              onDelete={() => handleDelete(r)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function RegionRow({
  region,
  onTranslate,
  onApprove,
  onDelete,
}: {
  region: OcrRegion;
  onTranslate: (t: string) => void;
  onApprove: () => void;
  onDelete: () => void;
}) {
  const [draft, setDraft] = useState(region.translated_text ?? "");
  const [editing, setEditing] = useState(false);

  const statusColor = STATUS_COLOR[region.status];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "70px 1fr 1fr 70px 130px",
        gap: 10,
        padding: "10px 14px",
        borderBottom: `1px solid ${theme.border}`,
        fontSize: 12,
        alignItems: "center",
        background: editing ? "rgba(125,211,252,0.05)" : "transparent",
      }}
    >
      {/* Frame preview */}
      <div
        style={{
          position: "relative",
          aspectRatio: "16/9",
          background: "#0d172e",
          border: `1px solid ${theme.border}`,
          borderRadius: 4,
          overflow: "hidden",
        }}
        title={`Frame #${region.frame_index}, ${(region.frame_ts_ms / 1000).toFixed(2)}s`}
      >
        <dir
          aria-hidden
          style={{
            position: "absolute",
            left: `${(region.bbox.x / 1920) * 100}%`,
            top: `${(region.bbox.y / 1080) * 100}%`,
            width: `${(region.bbox.w / 1920) * 100}%`,
            height: `${(region.bbox.h / 1080) * 100}%`,
            border: `2px solid ${statusColor}`,
            background: `${statusColor}22`,
            fontSize: 9,
            color: statusColor,
            padding: "1px 2px",
            overflow: "hidden",
          }}
        >
          #{region.frame_index}
        </dir>
        <div
          style={{
            position: "absolute",
            bottom: 2,
            right: 4,
            fontSize: 9,
            color: theme.textMuted,
          }}
        >
          {(region.frame_ts_ms / 1000).toFixed(1)}s
        </div>
      </div>

      {/* Source */}
      <div>
        <div style={{ fontSize: 9, color: theme.textMuted, fontWeight: 700, marginBottom: 2 }}>
          中文
        </div>
        <div style={{ fontFamily: "ui-monospace, monospace", color: theme.text }}>
          {region.source_text}
        </div>
        {region.confidence !== null && (
          <div style={{ fontSize: 10, color: theme.textDim, marginTop: 2 }}>
            conf {region.confidence.toFixed(2)}
          </div>
        )}
      </div>

      {/* Translation */}
      <div>
        <div style={{ fontSize: 9, color: theme.textMuted, fontWeight: 700, marginBottom: 2 }}>
          Tiếng Việt
        </div>
        {editing ? (
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={() => {
              onTranslate(draft);
              setEditing(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onTranslate(draft);
                setEditing(false);
              } else if (e.key === "Escape") {
                setDraft(region.translated_text ?? "");
                setEditing(false);
              }
            }}
            placeholder="Nhập bản dịch…"
            autoFocus
          />
        ) : (
          <button
            onClick={() => setEditing(true)}
            style={{
              background: "transparent",
              border: "none",
              textAlign: "left",
              cursor: "pointer",
              color: region.translated_text ? theme.text : theme.textDim,
              padding: 0,
              fontFamily: "inherit",
              fontSize: "inherit",
            }}
          >
            {region.translated_text || "Nhấp để dịch…"}
          </button>
        )}
      </div>

      {/* Status */}
      <div>
        <span
          style={{
            fontSize: 10,
            padding: "2px 6px",
            borderRadius: 3,
            background: `${statusColor}22`,
            color: statusColor,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          <StatusDot status={statusToDot(region.status)} /> {region.status}
        </span>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 4 }}>
        <Button
          size="sm"
          variant="primary"
          onClick={onApprove}
          disabled={region.status === "approved"}
        >
          ✓
        </Button>
        <Button size="sm" variant="danger" onClick={onDelete}>
          ✕
        </Button>
      </div>
    </div>
  );
}

const STATUS_COLOR: Record<string, string> = {
  pending: "#fbbf24",
  translated: "#60a5fa",
  approved: "#22c55e",
  rejected: "#ef4444",
};

function statusToDot(status: string): "pending" | "running" | "completed" | "failed" {
  if (status === "approved") return "completed";
  if (status === "rejected") return "failed";
  if (status === "translated") return "running";
  return "pending";
}
