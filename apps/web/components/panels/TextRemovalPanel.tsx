"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, EmptyState, SkeletonPanel } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  createTextRemovalJob,
  deleteTextRemovalJob,
  listTextRemovalJobs,
  type TextRemovalJob,
} from "@/lib/textRemoval";
import {
  listOcrRegions,
  type OcrRegion,
} from "@/lib/ocr";

interface Props {
  projectId: string;
}

const STRATEGIES = [
  { id: "telea", label: "OpenCV Telea", desc: "Nhanh, không cần GPU, chất lượng vừa" },
  { id: "inpaint_lama", label: "LaMa Inpaint", desc: "Chất lượng cao, cần GPU" },
  { id: "inpaint_anything", label: "Inpaint Anything", desc: "SAM-based, tốt nhất" },
] as const;

export function TextRemovalPanel({ projectId }: Props) {
  const { toast } = useToast();
  const [jobs, setJobs] = useState<TextRemovalJob[] | null>(null);
  const [regions, setRegions] = useState<OcrRegion[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState<(typeof STRATEGIES)[number]["id"]>("telea");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [running, setRunning] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [j, r] = await Promise.all([
        listTextRemovalJobs(projectId),
        listOcrRegions(projectId, undefined, 100).catch(() => ({ regions: [], total: 0 })),
      ]);
      setJobs(Array.isArray(j) ? j : []);
      setRegions(r.regions ?? []);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleRun() {
    if (selected.size === 0) {
      toast("Chọn ít nhất 1 region để xoá", "warn");
      return;
    }
    setRunning(true);
    try {
      const result = await createTextRemovalJob(projectId, {
        provider_id: "text_removal.mock",
        strategy,
        region_ids: Array.from(selected),
      });
      toast(
        `Đã tạo job ${result.job.id.slice(0, 8)}… (${result.region_count} regions, strategy=${strategy})`,
        "success",
      );
      setSelected(new Set());
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setRunning(false);
    }
  }

  async function handleDelete(j: TextRemovalJob) {
    if (!window.confirm("Xoá job này?")) return;
    try {
      await deleteTextRemovalJob(projectId, j.id);
      toast("Đã xoá", "info");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  if (loading && jobs === null) {
    return <SkeletonPanel title="Text Removal" rows={3} />;
  }

  return (
    <Card title="🧽 Text Removal" padded={false}>
      {/* Strategy + run */}
      <div
        style={{
          padding: 14,
          borderBottom: `1px solid ${theme.border}`,
          background: "#0d172e",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        <div style={{ fontSize: 11, color: theme.textMuted, fontWeight: 700, letterSpacing: 0.4 }}>
          CHIẾN LƯỢC
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {STRATEGIES.map((s) => (
            <button
              key={s.id}
              onClick={() => setStrategy(s.id)}
              style={{
                padding: "8px 12px",
                borderRadius: 6,
                border: `1px solid ${strategy === s.id ? theme.accentStrong : theme.border}`,
                background: strategy === s.id ? "rgba(125,211,252,0.08)" : theme.bgPanel,
                color: strategy === s.id ? theme.text : theme.textMuted,
                fontSize: 12,
                fontWeight: 600,
                textAlign: "left",
                cursor: "pointer",
                minWidth: 200,
              }}
            >
              <div>{s.label}</div>
              <div style={{ fontSize: 10, color: theme.textDim, marginTop: 2, fontWeight: 400 }}>
                {s.desc}
              </div>
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: theme.textMuted }}>
            Đã chọn: <strong style={{ color: theme.text }}>{selected.size}</strong> regions
          </span>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRun}
            disabled={running || selected.size === 0}
          >
            {running ? "⏳ Đang chạy…" : `▶ Chạy ${strategy}`}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelected(new Set())}
            disabled={selected.size === 0}
          >
            Bỏ chọn
          </Button>
        </div>
      </div>

      {/* Region picker */}
      {!regions || regions.length === 0 ? (
        <div style={{ padding: 16, color: theme.textMuted, fontSize: 13 }}>
          Chưa có OCR regions nào — chạy OCR trước để có danh sách.
        </div>
      ) : (
        <div
          style={{
            padding: 14,
            borderBottom: `1px solid ${theme.border}`,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 6,
            maxHeight: 240,
            overflowY: "auto",
          }}
        >
          {regions.map((r) => {
            const checked = selected.has(r.id);
            return (
              <label
                key={r.id}
                style={{
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                  padding: "4px 8px",
                  border: `1px solid ${checked ? theme.accentStrong : theme.border}`,
                  borderRadius: 4,
                  background: checked ? "rgba(125,211,252,0.08)" : theme.bgPanel,
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => {
                    setSelected((prev) => {
                      const next = new Set(prev);
                      if (e.target.checked) next.add(r.id);
                      else next.delete(r.id);
                      return next;
                    });
                  }}
                />
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  #{r.frame_index}: {r.source_text}
                </span>
              </label>
            );
          })}
        </div>
      )}

      {/* Jobs list */}
      <div style={{ padding: 14 }}>
        <div
          style={{ fontSize: 11, color: theme.textMuted, fontWeight: 700, marginBottom: 8, letterSpacing: 0.4 }}
        >
          JOBS ({jobs?.length ?? 0})
        </div>
        {!jobs || jobs.length === 0 ? (
          <EmptyState
            title="Chưa có job nào"
            description="Chọn regions ở trên + nhấn 'Chạy' để bắt đầu."
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {jobs.map((j) => (
              <JobRow key={j.id} job={j} onDelete={() => handleDelete(j)} />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

function JobRow({ job, onDelete }: { job: TextRemovalJob; onDelete: () => void }) {
  const c = STATUS_COLOR[job.status] ?? theme.text;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 100px 100px 100px 80px",
        gap: 8,
        padding: "8px 10px",
        background: theme.bgElevated,
        border: `1px solid ${theme.border}`,
        borderRadius: 4,
        alignItems: "center",
        fontSize: 12,
      }}
    >
      <div>
        <code style={{ fontSize: 11, color: theme.textMuted }}>{job.id.slice(0, 8)}…</code>
        <div style={{ fontSize: 10, color: theme.textDim, marginTop: 2 }}>
          {new Date(job.created_at).toLocaleString()} · asset {job.source_asset_id.slice(0, 8)}…
        </div>
      </div>
      <span
        style={{
          fontSize: 10,
          padding: "2px 6px",
          background: `${c}22`,
          color: c,
          borderRadius: 3,
          fontWeight: 700,
          textTransform: "uppercase",
          textAlign: "center",
        }}
      >
        {job.status}
      </span>
      <span style={{ fontSize: 11, color: theme.textMuted }}>{job.strategy || job.provider_id}</span>
      <span style={{ fontSize: 11, color: theme.textMuted }}>{job.region_ids.length} regions</span>
      <Button size="sm" variant="danger" onClick={onDelete}>
        Xoá
      </Button>
    </div>
  );
}

const STATUS_COLOR: Record<string, string> = {
  queued: theme.textMuted,
  running: theme.accent,
  completed: theme.success,
  failed: theme.danger,
};
