"use client";

import { useState } from "react";
import { useEditor } from "@/lib/store";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card, Select, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";

const STAGES = [
  { id: "analyze", label: "1. Phân tích Video & Cấu trúc âm thanh" },
  { id: "asr", label: "2. Nhận dạng giọng nói tiếng Trung (ASR)" },
  { id: "diarize", label: "3. Phân biệt người nói (Speaker Diarization)" },
  { id: "translate", label: "4. Dịch thuật tiếng Trung → Việt (AI Translation)" },
  { id: "qa", label: "5. Kiểm định chất lượng & Glossary (QA Check)" },
  { id: "voice", label: "6. Phân vai & Gán giọng đọc (Voice Assignment)" },
  { id: "tts", label: "7. Tổng hợp giọng nói tiếng Việt (TTS Synthesis)" },
  { id: "subtitle", label: "8. Tạo & Căn chỉnh phụ đề (Subtitle Generation)" },
  { id: "mix", label: "9. Tách nhạc nền & Trộn âm thanh (Audio Mixing)" },
  { id: "render", label: "10. Render & Xuất bản Video hoàn chỉnh" },
];

export function RenderPanel() {
  const projectId = useEditor((s) => s.projectId);
  const [resolution, setResolution] = useState("1080p");
  const [codec, setCodec] = useState("h264");
  const [audioMode, setAudioMode] = useState("dubbed");
  const [burnSubtitle, setBurnSubtitle] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onRender() {
    if (!projectId) return;
    setSubmitting(true);
    setError(null);
    try {
      const wf = await api.triggerWorkflow(projectId, { quality_mode: "high" });
      setResult(wf.workflow_id);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Card title="Các bước trong Quy trình Xử lý (Pipeline)">
        <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 6 }}>
          {STAGES.map((s, i) => (
            <li
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 12px",
                background: theme.bgElevated,
                borderRadius: 6,
                border: `1px solid ${theme.border}`,
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 999,
                  background: theme.bgPanel,
                  display: "grid",
                  placeItems: "center",
                  fontSize: 11,
                  fontWeight: 700,
                  color: theme.accent,
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{s.label}</span>
              <span style={{ marginLeft: "auto", fontSize: 11, display: "inline-flex", alignItems: "center", gap: 4 }}>
                <StatusDot status="ready" /> Sẵn sàng
              </span>
            </li>
          ))}
        </ol>
      </Card>

      <Card title="Cấu hình Render Video">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
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

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
          <div style={{ fontSize: 12, color: theme.textMuted }}>
            {result ? "✅ Tiến trình Render đã khởi tạo thành công" : "Sẵn sàng xuất bản video sau khi kiểm định"}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Button variant="primary" disabled={submitting || !projectId} onClick={onRender}>
              {submitting ? "⏳ Đang khởi tạo Render…" : "🎬 Bắt đầu Render Video"}
            </Button>
          </div>
        </div>

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
            ❌ Lỗi khởi chạy: {error}
          </div>
        )}
        {result && (
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
            <div>🚀 Workflow Render ID: <strong>{result}</strong></div>
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <Button size="sm" variant="ghost">📥 Tải Video MP4</Button>
              <Button size="sm" variant="ghost">📄 Tải Phụ đề SRT</Button>
              <Button size="sm" variant="ghost">📄 Tải Phụ đề VTT</Button>
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
