"use client";

import { useEffect, useState } from "react";
import { theme } from "@/lib/theme";
import { Button, StatusDot, EmptyState } from "@/components/ui";
import { useWorkflowStream } from "@/lib/useWorkflowStream";
import type { WorkflowStep } from "@/lib/types";
import { api } from "@/lib/api";

interface ProgressPanelProps {
  projectId: string;
  workflowId: string | null;
  onClose?: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  transcribe: "🎤 Phiên âm",
  diarize: "👥 Phân người nói",
  translate: "🌐 Dịch thuật",
  tts: "🔊 Tổng hợp giọng nói",
  align: "⏱️ Căn chỉnh thời gian",
  render: "🎬 Render video",
};

const getStageIcon = (name: string): string => {
  for (const [key, label] of Object.entries(STAGE_LABELS)) {
    if (name.toLowerCase().includes(key)) {
      return label.split(" ")[0] ?? "⚙️";
    }
  }
  return "⚙️";
};

const getStageLabel = (name: string): string => {
  for (const [key, label] of Object.entries(STAGE_LABELS)) {
    if (name.toLowerCase().includes(key)) {
      return label;
    }
  }
  return name;
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case "completed":
      return theme.success;
    case "failed":
      return theme.danger;
    case "processing":
      return theme.warn;
    default:
      return theme.textMuted;
  }
};

export function ProgressPanel({ projectId, workflowId, onClose }: ProgressPanelProps) {
  const { steps, status: streamStatus, retryCount, error, lastError } = useWorkflowStream(workflowId);
  const [workflowStatus, setWorkflowStatus] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Poll workflow overall status
  useEffect(() => {
    if (!workflowId || !projectId) return;
    
    let cancelled = false;
    const pollStatus = async () => {
      try {
        const wf = await api.getWorkflow(projectId, workflowId);
        if (!cancelled) {
          setWorkflowStatus(wf.status);
        }
        
        // Continue polling if processing
        if (wf.status === "processing" && !cancelled) {
          setTimeout(pollStatus, 5000);
        }
      } catch (err) {
        console.error("Failed to poll workflow status:", err);
      }
    };
    
    pollStatus();
    
    return () => {
      cancelled = true;
    };
  }, [projectId, workflowId]);

  const handleRefresh = async () => {
    if (!projectId || !workflowId) return;
    setIsRefreshing(true);
    try {
      const wf = await api.getWorkflow(projectId, workflowId);
      setWorkflowStatus(wf.status);
    } catch (err) {
      console.error("Failed to refresh workflow:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!workflowId) {
    return (
      <div style={{ padding: 16 }}>
        <EmptyState
          title="Chưa có workflow nào đang chạy"
          description="Chuyển sang tab Render để bắt đầu xử lý video."
        />
      </div>
    );
  }

  const orderedSteps = [...steps].sort((a, b) => {
    const order = ["transcribe", "diarize", "translate", "tts", "align", "render"];
    const ai = order.findIndex((k) => a.name.toLowerCase().includes(k));
    const bi = order.findIndex((k) => b.name.toLowerCase().includes(k));
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });

  const completedSteps = orderedSteps.filter((s) => s.status === "completed").length;
  const totalSteps = orderedSteps.length || 1;
  const overallPct = Math.round((completedSteps / totalSteps) * 100);
  const pipelineDone = workflowStatus === "ready" || workflowStatus === "completed";
  const pipelineFailed = workflowStatus === "failed";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: theme.bg,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: `1px solid ${theme.border}`,
          background: theme.bgElevated,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: theme.text, marginBottom: 4 }}>
            📊 Tiến trình Workflow
          </div>
          <div style={{ fontSize: 11, color: theme.textMuted }}>
            Workflow ID: {workflowId.substring(0, 8)}...
          </div>
        </div>
        <Button size="sm" variant="ghost" onClick={handleRefresh} disabled={isRefreshing}>
          {isRefreshing ? "⏳" : "🔄"} Làm mới
        </Button>
        {onClose && (
          <Button size="sm" variant="ghost" onClick={onClose}>
            ✕
          </Button>
        )}
      </div>

      {/* Overall progress bar */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: `1px solid ${theme.border}`,
          background: theme.bgElevated,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <StatusDot
              status={
                pipelineDone ? "completed" : pipelineFailed ? "failed" : "processing"
              }
            />
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              {pipelineDone
                ? "✅ Hoàn tất"
                : pipelineFailed
                  ? "❌ Thất bại"
                  : `⏳ Đang xử lý`}
            </span>
          </div>
          <span style={{ fontSize: 12, fontWeight: 600, color: theme.textMuted }}>
            {completedSteps}/{totalSteps} bước ({overallPct}%)
          </span>
        </div>
        <div
          style={{
            height: 8,
            background: theme.bgPanel,
            borderRadius: 4,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              background: pipelineDone
                ? theme.success
                : pipelineFailed
                  ? theme.danger
                  : theme.accent,
              width: `${overallPct}%`,
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>

      {/* Stream status */}
      {(streamStatus === "error" || lastError) && (
        <div
          style={{
            padding: "8px 16px",
            background: "#450a0a",
            color: theme.danger,
            fontSize: 12,
            borderBottom: `1px solid #7f1d1d`,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span>⚠️</span>
          <span style={{ flex: 1 }}>{lastError || "Lỗi kết nối stream"}</span>
          {retryCount > 0 && (
            <span style={{ fontSize: 11, opacity: 0.8 }}>
              (Đã thử lại {retryCount} lần)
            </span>
          )}
        </div>
      )}

      {/* Step grid */}
      <div
        style={{
          flex: 1,
          overflow: "auto",
          padding: 16,
        }}
      >
        {orderedSteps.length === 0 ? (
          <EmptyState
            title="Đang chờ dữ liệu workflow"
            description="Backend đang khởi tạo workflow. Vui lòng đợi trong giây lát..."
          />
        ) : (
          <div
            style={{
              display: "grid",
              gap: 12,
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            }}
          >
            {orderedSteps.map((step) => {
              const pct = Math.round((step.progress_pct || 0));
              const statusColor = getStatusColor(step.status);

              return (
                <div
                  key={step.name}
                  style={{
                    background: theme.bgElevated,
                    border: `1px solid ${theme.border}`,
                    borderRadius: 8,
                    padding: 12,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <span style={{ fontSize: 18 }}>{getStageIcon(step.name)}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          color: theme.text,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {getStageLabel(step.name)}
                      </div>
                      <div
                        style={{
                          fontSize: 10,
                          color: theme.textMuted,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {step.name}
                      </div>
                    </div>
                    <StatusDot status={step.status} />
                  </div>

                  <div
                    style={{
                      height: 6,
                      background: theme.bgPanel,
                      borderRadius: 3,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        background: statusColor,
                        width: `${pct}%`,
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        color: statusColor,
                        fontWeight: 600,
                        textTransform: "capitalize",
                      }}
                    >
                      {step.status}
                    </span>
                    <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>
                      {pct}%
                    </span>
                  </div>

                  {step.progress_message && step.status === "failed" && (
                    <div
                      style={{
                        fontSize: 11,
                        color: theme.danger,
                        background: "#450a0a",
                        padding: "6px 8px",
                        borderRadius: 4,
                        border: "1px solid #7f1d1d",
                        marginTop: 4,
                      }}
                    >
                      {step.progress_message}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
