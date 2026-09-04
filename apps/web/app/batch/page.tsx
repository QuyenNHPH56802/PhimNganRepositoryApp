"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button, Card, EmptyState, Modal, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  createBatch,
  deleteBatch,
  getBatch,
  type BatchItemInput,
  type BatchStatus,
} from "@/lib/batch";

const POLL_MS = 2000;

interface PendingItem extends BatchItemInput {
  key: string;
}

export default function BatchPage() {
  const { toast } = useToast();
  const [items, setItems] = useState<PendingItem[]>([
    { key: crypto.randomUUID(), title: "", asset_filename: "" },
  ]);
  const [maxConcurrency, setMaxConcurrency] = useState(3);
  const [submitting, setSubmitting] = useState(false);
  const [batches, setBatches] = useState<BatchStatus[]>([]);
  const [polling, setPolling] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function addItem() {
    setItems((prev) => [...prev, { key: crypto.randomUUID(), title: "", asset_filename: "" }]);
  }

  function removeItem(key: string) {
    setItems((prev) => (prev.length === 1 ? prev : prev.filter((it) => it.key !== key)));
  }

  function updateItem(key: string, patch: Partial<BatchItemInput>) {
    setItems((prev) => prev.map((it) => (it.key === key ? { ...it, ...patch } : it)));
  }

  async function handleSubmit() {
    const valid = items.filter((it) => it.title.trim() && it.asset_filename.trim());
    if (valid.length === 0) {
      toast("Cần nhập ít nhất 1 item hợp lệ (title + filename)", "warn");
      return;
    }
    setSubmitting(true);
    try {
      const result = await createBatch({
        items: valid.map(({ key, ...rest }) => rest),
        max_concurrency: maxConcurrency,
        auto_start: true,
      });
      toast(`Đã queue batch với ${result.accepted} items`, "success");
      // Reset form
      setItems([{ key: crypto.randomUUID(), title: "", asset_filename: "" }]);
      // Start polling
      startPolling(result.batch_id);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSubmitting(false);
    }
  }

  const startPolling = useCallback((batchId: string) => {
    setPolling(batchId);
    if (pollRef.current) clearInterval(pollRef.current);
    const tick = async () => {
      try {
        const status = await getBatch(batchId);
        setBatches((prev) => {
          const idx = prev.findIndex((b) => b.batch_id === batchId);
          if (idx === -1) return [status, ...prev];
          const next = [...prev];
          next[idx] = status;
          return next;
        });
        // Stop polling if finished.
        if (
          status.state === "completed" ||
          status.state === "failed" ||
          status.state === "partial_failure"
        ) {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setPolling(null);
          toast(`Batch kết thúc: ${status.state}`, "info");
        }
      } catch {
        if (pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
        setPolling(null);
      }
    };
    tick();
    pollRef.current = setInterval(tick, POLL_MS);
  }, [toast]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function handleDeleteBatch(id: string) {
    if (!window.confirm("Xoá batch này khỏi danh sách?")) return;
    try {
      await deleteBatch(id);
      setBatches((prev) => prev.filter((b) => b.batch_id !== id));
      toast("Đã xoá batch", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header>
        <h1 style={{ fontSize: 22, margin: 0 }}>⚡ Batch Processing</h1>
        <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
          Submit nhiều video vào queue xử lý song song (max 3 đồng thời). Theo dõi tiến trình theo batch.
        </p>
      </header>

      <Card title="Tạo batch mới" padded>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {items.map((it, i) => (
              <div
                key={it.key}
                style={{
                  display: "grid",
                  gridTemplateColumns: "30px 1.4fr 1.6fr 1fr 1fr 30px",
                  gap: 8,
                  alignItems: "center",
                  padding: 10,
                  background: theme.bgElevated,
                  border: `1px solid ${theme.border}`,
                  borderRadius: 6,
                }}
              >
                <span style={{ color: theme.textMuted, fontWeight: 600, fontSize: 12 }}>#{i + 1}</span>
                <input
                  placeholder="Tiêu đề project"
                  value={it.title}
                  onChange={(e) => updateItem(it.key, { title: e.target.value })}
                  style={inputStyle}
                />
                <input
                  placeholder="Tên file (asset_filename)"
                  value={it.asset_filename}
                  onChange={(e) => updateItem(it.key, { asset_filename: e.target.value })}
                  style={inputStyle}
                />
                <select
                  value={it.quality_mode ?? "balanced"}
                  onChange={(e) => updateItem(it.key, { quality_mode: e.target.value })}
                  style={inputStyle}
                >
                  <option value="fast">Fast</option>
                  <option value="balanced">Balanced</option>
                  <option value="high">High</option>
                </select>
                <select
                  value={it.language_profile ?? "zh-vi"}
                  onChange={(e) => updateItem(it.key, { language_profile: e.target.value })}
                  style={inputStyle}
                >
                  <option value="zh-vi">Chinese → Vietnamese</option>
                  <option value="zh-en">Chinese → English</option>
                  <option value="en-vi">English → Vietnamese</option>
                </select>
                <button
                  onClick={() => removeItem(it.key)}
                  disabled={items.length === 1}
                  aria-label="Xoá item"
                  style={{
                    background: "transparent",
                    border: "none",
                    color: items.length === 1 ? theme.textDim : theme.danger,
                    cursor: items.length === 1 ? "not-allowed" : "pointer",
                    fontSize: 16,
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <Button size="sm" variant="ghost" onClick={addItem}>
              + Thêm item
            </Button>
            <label style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center", fontSize: 12 }}>
              <span style={{ color: theme.textMuted }}>Concurrency:</span>
              <input
                type="number"
                min={1}
                max={16}
                value={maxConcurrency}
                onChange={(e) => setMaxConcurrency(parseInt(e.target.value || "3", 10))}
                style={{ ...inputStyle, width: 60 }}
              />
            </label>
            <Button variant="primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? "…" : `Queue ${items.length} items →`}
            </Button>
          </div>
        </div>
      </Card>

      {/* Polling banner */}
      {polling && (
        <div
          style={{
            padding: "8px 12px",
            background: "rgba(125,211,252,0.1)",
            border: `1px solid ${theme.accent}`,
            borderRadius: 6,
            fontSize: 12,
            color: theme.accent,
          }}
        >
          ⏳ Đang theo dõi batch <code>{polling}</code> — cập nhật mỗi {POLL_MS / 1000}s…
        </div>
      )}

      {/* Active batches */}
      {batches.length === 0 ? (
        <EmptyState
          title="Chưa có batch nào"
          description="Submit 1 batch ở trên để bắt đầu."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {batches.map((b) => (
            <Card
              key={b.batch_id}
              title={
                <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <StatusDot
                    status={
                      b.state === "completed"
                        ? "completed"
                        : b.state === "failed"
                          ? "failed"
                          : b.state === "partial_failure"
                            ? "processing"
                            : b.state === "running"
                              ? "pending"
                              : "pending"
                    }
                  />
                  <code style={{ fontSize: 12, color: theme.textMuted }}>{b.batch_id.slice(0, 12)}…</code>
                  <span style={{ fontSize: 11, color: theme.textDim, fontWeight: 400 }}>
                    {new Date(b.created_at).toLocaleString()}
                  </span>
                </span>
              }
              action={
                <Button size="sm" variant="danger" onClick={() => handleDeleteBatch(b.batch_id)}>
                  Xoá
                </Button>
              }
              padded={false}
            >
              <div style={{ padding: 14 }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, minmax(0,1fr))",
                    gap: 12,
                    marginBottom: 12,
                  }}
                >
                  <SummaryMini label="State" value={b.state} color={stateColor(b.state, theme)} />
                  <SummaryMini
                    label="Completed"
                    value={`${b.summary.completed}`}
                    color={theme.success}
                  />
                  <SummaryMini
                    label="Failed"
                    value={`${b.summary.failed}`}
                    color={theme.danger}
                  />
                  <SummaryMini
                    label="Pending"
                    value={`${b.summary.pending ?? 0}`}
                    color={theme.warn}
                  />
                </div>

                <div
                  role="table"
                  aria-label="Batch items"
                  style={{
                    border: `1px solid ${theme.border}`,
                    borderRadius: 6,
                    overflow: "hidden",
                  }}
                >
                  <div
                    role="row"
                    style={{
                      display: "grid",
                      gridTemplateColumns: "40px 1.4fr 100px 1fr 80px",
                      gap: 8,
                      padding: "8px 10px",
                      background: "#0d172e",
                      fontSize: 11,
                      fontWeight: 700,
                      color: theme.textMuted,
                      textTransform: "uppercase",
                    }}
                  >
                    <span>#</span>
                    <span>Title</span>
                    <span>Status</span>
                    <span>Project / Workflow</span>
                    <span></span>
                  </div>
                  {b.items.map((it) => (
                    <div
                      role="row"
                      key={it.item_index}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "40px 1.4fr 100px 1fr 80px",
                        gap: 8,
                        padding: "8px 10px",
                        borderTop: `1px solid ${theme.border}`,
                        fontSize: 12,
                        alignItems: "center",
                      }}
                    >
                      <span style={{ color: theme.textDim }}>{it.item_index + 1}</span>
                      <span>{it.title}</span>
                      <span
                        style={{
                          color: itemColor(it.status, theme),
                          fontWeight: 700,
                          fontSize: 11,
                        }}
                      >
                        {it.status}
                      </span>
                      <span
                        style={{
                          color: theme.textMuted,
                          fontFamily: "ui-monospace",
                          fontSize: 10,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {it.project_id ? `${it.project_id.slice(0, 8)}…` : "—"}
                      </span>
                      <span>
                        {it.project_id && (
                          <Link href={`/projects/${it.project_id}/workspace`} style={{ fontSize: 11 }}>
                            Mở →
                          </Link>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function SummaryMini({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      style={{
        background: theme.bgElevated,
        padding: "8px 12px",
        borderRadius: 6,
        border: `1px solid ${theme.border}`,
      }}
    >
      <div style={{ fontSize: 10, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.4 }}>
        {label}
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, color, marginTop: 2 }}>{value}</div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: theme.bgPanel,
  border: `1px solid ${theme.border}`,
  color: theme.text,
  padding: "6px 10px",
  borderRadius: 4,
  fontSize: 12,
};

function stateColor(state: string, theme: Record<string, string>) {
  if (state === "completed") return theme.success;
  if (state === "failed") return theme.danger;
  if (state === "partial_failure") return theme.warn;
  return theme.accent;
}

function itemColor(status: string, theme: Record<string, string>) {
  if (status === "completed") return theme.success;
  if (status === "failed") return theme.danger;
  if (status === "running") return theme.accent;
  return theme.textMuted;
}
