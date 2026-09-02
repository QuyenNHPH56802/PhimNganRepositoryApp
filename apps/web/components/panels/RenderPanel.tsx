"use client";

import { useEffect, useState, useCallback } from "react";
import { useEditor } from "@/lib/store";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card, Select, StatusDot } from "@/components/ui";
import { API_BASE_URL } from "@/lib/types";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";

const STAGES = [
  { id: "normalize_chinese", label: "1. Chuẩn hóa tiếng Trung", step: "normalize" },
  { id: "translate_segments", label: "2. Dịch thuật tiếng Trung → Việt", step: "translate" },
  { id: "translation_qa", label: "3. Kiểm định chất lượng dịch thuật", step: "qa" },
  { id: "subtitle_segment", label: "4. Tạo phụ đề", step: "subtitle" },
  { id: "tts_synthesize", label: "5. Tổng hợp giọng nói (TTS)", step: "tts" },
  { id: "dubbing_align", label: "6. Căn chỉnh lồng tiếng", step: "align" },
  { id: "audio_mix", label: "7. Trộn âm thanh", step: "mix" },
  { id: "render_build", label: "8. Render video hoàn chỉnh", step: "render" },
];

const QUALITY_MODES: { value: "fast" | "balanced" | "high"; label: string; description: string }[] = [
  { value: "fast", label: "Nhanh", description: "Chất lượng tốt, xử lý nhanh" },
  { value: "balanced", label: "Cân bằng", description: "Cân bằng chất lượng và tốc độ" },
  { value: "high", label: "Chất lượng cao", description: "Chất lượng tốt nhất, xử lý chậm hơn" },
];

// Map workflow step names to our stage IDs
function mapStepToStage(stepName: string): string | null {
  const name = stepName.toLowerCase();
  if (name.includes("normalize") || name.includes("transcribe")) return "normalize_chinese";
  if (name.includes("translate") || name.includes("translation")) return "translate_segments";
  if (name.includes("qa") || name.includes("quality") || name.includes("review")) return "translation_qa";
  if (name.includes("subtitle")) return "subtitle_segment";
  if (name.includes("tts") || name.includes("synthesize") || name.includes("voice")) return "tts_synthesize";
  if (name.includes("align") || name.includes("dub")) return "dubbing_align";
  if (name.includes("mix") || name.includes("audio")) return "audio_mix";
  if (name.includes("render") || name.includes("build") || name.includes("export")) return "render_build";
  return null;
}

export function RenderPanel() {
  const projectId = useEditor((s) => s.projectId);
  const audio = useEditor((s) => s.audio);
  const setRenderedVideoSrc = useEditor((s) => s.setRenderedVideoSrc);
  const [resolution, setResolution] = useState("1080p");
  const [codec, setCodec] = useState("h264");
  const [audioMode, setAudioMode] = useState("dubbed");
  const [burnSubtitle, setBurnSubtitle] = useState(true);
  const [qualityMode, setQualityMode] = useState<"fast" | "balanced" | "high">("balanced");
  const [submitting, setSubmitting] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<{ workflow_id: string; run_id: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<Record<string, string>>({});
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [renderProgress, setRenderProgress] = useState<string>("");
  const { toast } = useToast();

  // Render Nhanh is only useful when TTS audio exists (audioMode === "dubbed"
  // mixes TTS into the output). For "original" sub-only mode, audio can be
  // empty and FFmpeg will fall back to the source track.
  const ttsAudioEmpty = audio.length === 0;
  const renderDisabledReason =
    ttsAudioEmpty && audioMode === "dubbed"
      ? "Cần sinh TTS trước (bảng Âm thanh đang trống). Chuyển 'Chế độ âm thanh' sang 'Giữ tiếng gốc' nếu chỉ cần phụ đề."
      : null;

  // Poll workflow status — guarded by `cancelledRef` so the recursive timer
  // chain bails out cleanly when a new poll starts or the panel unmounts.
  const cancelledRef = { current: false };
  const pollStatus = useCallback(async (workflowId: string) => {
    if (!projectId || cancelledRef.current) return;

    try {
      const status = await api.getWorkflow(projectId, workflowId);
      if (cancelledRef.current) return;
      if (status?.status === "ready") {
        setIsComplete(true);
        setRenderProgress("");
        const assetUrl = await api.getAssetUrl(projectId);
        if (assetUrl?.rendered_url) {
          setDownloadUrl(assetUrl.rendered_url);
          setRenderedVideoSrc(assetUrl.rendered_url);
        }
        return;
      }

      if (status?.status === "failed") {
        setError("Workflow thất bại");
        setRenderProgress("");
        return;
      }

      // Continue polling after delay; re-check cancellation right before
      // recursing so a late cancellation doesn't schedule another fetch.
      await new Promise((resolve) => setTimeout(resolve, 3000));
      if (cancelledRef.current) return;
      return pollStatus(workflowId);
    } catch (err) {
      console.error("Poll status error:", err);
    }
  }, [projectId]);

  // Cleanup polling on unmount or when projectId changes
  useEffect(() => {
    cancelledRef.current = false;

    if (workflowResult?.workflow_id && !isComplete) {
      pollStatus(workflowResult.workflow_id);
    }

    return () => {
      cancelledRef.current = true;
    };
  }, [workflowResult?.workflow_id, isComplete, pollStatus]);

  // Fetch initial workflow status
  useEffect(() => {
    if (!projectId) return;

    const pid = projectId;

    async function fetchStatus() {
      try {
        // Try to get workflow by using the expected workflow_id pattern: project-{projectId}
        const wf = await api.getWorkflow(pid, `project-${pid}`).catch(() => null);
        if (wf) {
          setWorkflowResult({ workflow_id: wf.workflow_id, run_id: wf.run_id });
          if (wf.status === "ready") {
            setIsComplete(true);
            // Check for rendered video
            const assetUrl = await api.getAssetUrl(pid);
            if (assetUrl?.rendered_url) {
              setDownloadUrl(assetUrl.rendered_url);
            }
          }

          // Get steps using the correct workflow_id
          try {
            const steps = await api.listWorkflowSteps(pid, wf.workflow_id);
            const statusMap: Record<string, string> = {};
            steps.forEach((s: any) => {
              const stageId = mapStepToStage(s.name);
              if (stageId) {
                statusMap[stageId] = s.status;
              }
            });
            setWorkflowStatus(statusMap);
          } catch { }
        }
      } catch { }
    }

    fetchStatus();
  }, [projectId]);

  // Quick render using direct FFmpeg
  async function onQuickRender() {
    if (!projectId) return;
    setRendering(true);
    setError(null);
    setRenderProgress("Đang khởi tạo render...");
    
    try {
      const result = await api.renderVideo(projectId, {
        resolution,
        codec,
        audio_mode: audioMode,
        burn_subtitle: burnSubtitle,
        quality_mode: qualityMode,
      });
      
      if (result.ok && result.rendered_url) {
        setDownloadUrl(result.rendered_url);
        setRenderedVideoSrc(result.rendered_url);
        setIsComplete(true);
        setRenderProgress("");
        toast("Render thành công!", "success");
      } else {
        setError(result.error || "Render thất bại");
        setRenderProgress("");
        toast(`Render thất bại: ${result.error ?? "không rõ nguyên nhân"}`, "danger");
      }
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err));
      setRenderProgress("");
    } finally {
      setRendering(false);
    }
  }

  // Full pipeline using Temporal workflow
  async function onFullPipeline() {
    if (!projectId) return;
    setSubmitting(true);
    setError(null);
    setRenderProgress("Đang khởi tạo pipeline...");
    try {
      const wf = await api.triggerWorkflow(projectId, { quality_mode: qualityMode });
      setWorkflowResult(wf);
      setRenderProgress("Pipeline đang chạy...");
      pollStatus(wf.workflow_id);
      toast("Pipeline đã khởi động", "success");
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err));
      setRenderProgress("");
    } finally {
      setSubmitting(false);
    }
  }

  function downloadVideo() {
    if (downloadUrl) {
      window.open(`/api/proxy-video?path=${encodeURIComponent(downloadUrl)}`, "_blank");
    }
  }

  async function downloadSubtitles(format: "srt" | "vtt") {
    if (!projectId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/projects/${projectId}/subtitles/export?format=${format}`);
      if (!res.ok) {
        setError(`Không thể tải phụ đề ${format.toUpperCase()}: HTTP ${res.status}`);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `subtitles.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Card title="Tiến trình xử lý Pipeline">
        <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 6 }}>
          {STAGES.map((s, i) => {
            const status = workflowStatus[s.id] || (isComplete ? "ready" : "pending");
            const isReady = status === "ready";
            const isProcessing = status === "processing" || status === "running";
            
            return (
              <li
                key={s.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 12px",
                  background: isReady ? "rgba(16, 185, 129, 0.08)" : isProcessing ? "rgba(251, 191, 36, 0.08)" : theme.bgElevated,
                  borderRadius: 6,
                  border: `1px solid ${isReady ? "#10b981" : isProcessing ? "#fbbf24" : theme.border}`,
                }}
              >
                <span
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 999,
                    background: isReady ? theme.success : isProcessing ? theme.warn : theme.bgPanel,
                    display: "grid",
                    placeItems: "center",
                    fontSize: 11,
                    fontWeight: 700,
                    color: isReady || isProcessing ? "#fff" : theme.accent,
                  }}
                >
                  {isReady ? "✓" : isProcessing ? "⟳" : i + 1}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{s.label}</span>
                <span style={{ marginLeft: "auto", fontSize: 11, display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <StatusDot status={isReady ? "ready" : isProcessing ? "warn" : "pending"} />
                  {isReady ? "Hoàn tất" : isProcessing ? "Đang xử lý..." : "Chờ"}
                </span>
              </li>
            );
          })}
        </ol>
      </Card>

      <Card title="Cấu hình Render Video">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Chế độ chất lượng">
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {QUALITY_MODES.map((q) => (
                <label
                  key={q.value}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 10px",
                    borderRadius: 6,
                    cursor: "pointer",
                    background: qualityMode === q.value ? "rgba(125,211,252,0.08)" : "transparent",
                    border: `1px solid ${qualityMode === q.value ? theme.accent : theme.border}`,
                  }}
                >
                  <input
                    type="radio"
                    name="quality"
                    value={q.value}
                    checked={qualityMode === q.value}
                    onChange={() => setQualityMode(q.value)}
                    style={{ accentColor: theme.accent }}
                  />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{q.label}</div>
                    <div style={{ fontSize: 11, color: theme.textMuted }}>{q.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </Field>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Field label="Độ phân giải video">
              <Select value={resolution} onChange={(e) => setResolution(e.target.value)}>
                <option value="720p">HD (720p)</option>
                <option value="1080p">Full HD (1080p) — Khuyên dùng</option>
                <option value="4k">4K Ultra HD (2160p)</option>
                <option value="source">Giữ nguyên theo video gốc</option>
              </Select>
            </Field>
            <Field label="Chuẩn nén Video (Codec)">
              <Select value={codec} onChange={(e) => setCodec(e.target.value)}>
                <option value="h264">H.264 / AVC (Tương thích tốt nhất)</option>
                <option value="hevc">H.265 / HEVC (Dung lượng nhỏ hơn)</option>
                <option value="copy">Copy Stream gốc (Nhanh nhất)</option>
              </Select>
            </Field>
            <Field label="Chế độ âm thanh">
              <Select value={audioMode} onChange={(e) => setAudioMode(e.target.value)}>
                <option value="dubbed">Lồng tiếng Việt + Trộn Nhạc nền gốc (Dubbing)</option>
                <option value="original">Giữ tiếng gốc Trung + Phụ đề Việt (Sub-only)</option>
                <option value="dual">Âm thanh kép (Dual Track Audio)</option>
              </Select>
            </Field>
            <Field label="Tùy chọn phụ đề">
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer", marginTop: 4 }}>
                <input type="checkbox" checked={burnSubtitle} onChange={(e) => setBurnSubtitle(e.target.checked)} />
                <span>Nhúng phụ đề cứng (Hardsub) trực tiếp vào Video</span>
              </label>
            </Field>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
          <div style={{ fontSize: 12, color: theme.textMuted }}>
            {renderProgress || (workflowResult ? `✅ Pipeline ID: ${workflowResult.workflow_id}` : "Sẵn sàng xuất bản video sau khi kiểm định")}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {isComplete && downloadUrl && (
              <Button size="sm" variant="primary" onClick={downloadVideo}>
                📥 Tải Video MP4
              </Button>
            )}
            <Button
              variant="ghost"
              disabled={submitting || rendering || isComplete || !!renderDisabledReason}
              onClick={onQuickRender}
              title={renderDisabledReason ?? "Render nhanh với FFmpeg trực tiếp"}
            >
              {rendering ? "⏳ Đang render..." : "⚡ Render Nhanh"}
            </Button>
            <Button
              variant="primary"
              disabled={submitting || rendering || isComplete || !!renderDisabledReason}
              onClick={onFullPipeline}
              title={renderDisabledReason ?? undefined}
            >
              {submitting
                ? "⏳ Đang khởi tạo..."
                : isComplete
                  ? "✅ Đã hoàn thành"
                  : "🎬 Full Pipeline"}
            </Button>
            {isComplete && (
              <Button
                variant="ghost"
                onClick={() => {
                  // Reset render state so the user can re-run the pipeline
                  // after tweaking config.
                  setIsComplete(false);
                  setDownloadUrl(null);
                  setWorkflowResult(null);
                  setWorkflowStatus({});
                  toast("Đã reset — có thể render lại với cấu hình mới", "info");
                }}
                title="Reset trạng thái để render lại"
              >
                🔄 Render lại
              </Button>
            )}
          </div>
        </div>

        {renderDisabledReason && (
          <div
            style={{
              marginTop: 12,
              background: "#3b1d05",
              color: theme.warn,
              padding: 10,
              borderRadius: 6,
              fontSize: 12,
              border: "1px solid #7c2d12",
            }}
          >
            ⚠ {renderDisabledReason}
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: 12,
              background: "#450a0a",
              color: theme.danger,
              padding: 12,
              borderRadius: 6,
              fontSize: 12,
              border: "1px solid #7f1d1d",
            }}
          >
            ❌ Lỗi: {error}
          </div>
        )}
        
        {isComplete && (
          <div
            style={{
              marginTop: 12,
              background: "#052e16",
              color: theme.success,
              padding: 12,
              borderRadius: 6,
              fontSize: 12,
              border: "1px solid #14532d",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            <div>🎉 Video đã được render thành công!</div>
            <div style={{ display: "flex", gap: 8 }}>
              <Button size="sm" variant="primary" onClick={downloadVideo}>
                📥 Tải Video MP4
              </Button>
              <Button size="sm" variant="ghost" onClick={() => downloadSubtitles("srt")}>📄 Tải Phụ đề SRT</Button>
              <Button size="sm" variant="ghost" onClick={() => downloadSubtitles("vtt")}>📄 Tải Phụ đề VTT</Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}
