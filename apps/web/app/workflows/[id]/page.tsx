"use client";

import { useState } from "react";
import { useWorkflowStream, WorkflowStep } from "@/lib/useWorkflowStream";
import { Button, Badge } from "@/components/ui";
import { theme } from "@/lib/theme";

const STATUS_COLORS: Record<WorkflowStep["status"], { bg: string; label: string }> = {
  queued: { bg: "#64748b", label: "Đang chờ" },
  processing: { bg: "#f59e0b", label: "Đang xử lý" },
  ready: { bg: "#22c55e", label: "Sẵn sàng" },
  failed: { bg: "#ef4444", label: "Thất bại" },
};

export default function WorkflowProgressPage({ params }: { params: { id: string } }) {
  const { steps, status, retryCount } = useWorkflowStream(params.id);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancel() {
    setCancelling(true);
    setError(null);
    try {
      const response = await fetch(`/api/workflows/${params.id}/cancel`, { method: "POST" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        // 2xx means backend actually accepted the cancellation; anything else
        // is a real failure (e.g. 404 when the workflow is already gone).
        const message =
          typeof data === "object" && data !== null && "error" in data
            ? String((data as { error: unknown }).error)
            : `HTTP ${response.status}`;
        setError(message);
      }
      // Successful cancellation produces no UI signal — the SSE stream will
      // update the steps and the user sees progress stop on its own.
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16, maxWidth: 800 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>Tiến trình Workflow</h1>
        <Button
          variant="danger"
          onClick={cancel}
          disabled={cancelling}
        >
          {cancelling ? "⏳ Đang huỷ…" : "⛔ Huỷ workflow"}
        </Button>
      </header>
      <div style={{ fontSize: 13, color: theme.textMuted }}>
        Trạng thái stream: <strong style={{ color: theme.text }}>{status}</strong>
      </div>
      {error && (
        <div style={{ background: "#450a0a", color: theme.danger, padding: 12, borderRadius: 6, fontSize: 12, border: "1px solid #7f1d1d" }}>
          ❌ Lỗi: {error}
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {steps.map((step) => (
          <div
            key={step.name}
            style={{
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: 14,
              background: theme.bgPanel,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ fontWeight: 600, fontSize: 14 }}>{step.name}</span>
              <Badge
                tone={step.status === "ready" ? "success" : step.status === "failed" ? "danger" : step.status === "processing" ? "warn" : "neutral"}
              >
                {STATUS_COLORS[step.status]?.label ?? step.status}
              </Badge>
            </div>
            <div
              style={{
                width: "100%",
                height: 6,
                background: theme.bgElevated,
                borderRadius: 3,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${step.progress_pct}%`,
                  height: "100%",
                  background: step.status === "failed" ? theme.danger : theme.accent,
                  transition: "width 200ms ease",
                }}
              />
            </div>
            {step.progress_message && (
              <p style={{ fontSize: 11, color: theme.textMuted, marginTop: 6 }}>
                {step.progress_message}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
