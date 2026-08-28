"use client";

import { useState } from "react";
import { useEditor } from "@/lib/store";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card, Select, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";

const STAGES = [
  { id: "analyze", label: "Analyze" },
  { id: "asr", label: "ASR" },
  { id: "diarize", label: "Diarization" },
  { id: "translate", label: "Translation" },
  { id: "qa", label: "QA" },
  { id: "voice", label: "Voice Assignment" },
  { id: "tts", label: "TTS" },
  { id: "subtitle", label: "Subtitle" },
  { id: "mix", label: "Audio Mix" },
  { id: "render", label: "Render" },
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
      <Card title="Pipeline stages">
        <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 6 }}>
          {STAGES.map((s, i) => (
            <li
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 10px",
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
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{s.label}</span>
              <span style={{ marginLeft: "auto" }}>
                <StatusDot status="ready" /> ready
              </span>
            </li>
          ))}
        </ol>
      </Card>

      <Card title="Render settings">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Resolution">
            <Select value={resolution} onChange={(e) => setResolution(e.target.value)}>
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
              <option value="4k">4K</option>
              <option value="source">Theo video gốc</option>
            </Select>
          </Field>
          <Field label="Video codec">
            <Select value={codec} onChange={(e) => setCodec(e.target.value)}>
              <option value="h264">H.264</option>
              <option value="hevc">HEVC</option>
              <option value="copy">Copy stream</option>
            </Select>
          </Field>
          <Field label="Audio mode">
            <Select value={audioMode} onChange={(e) => setAudioMode(e.target.value)}>
              <option value="dubbed">Lồng tiếng (dub)</option>
              <option value="original">Giữ nguyên (sub-only)</option>
              <option value="dual">Dual track</option>
            </Select>
          </Field>
          <Field label="Burn subtitle">
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
              <input type="checkbox" checked={burnSubtitle} onChange={(e) => setBurnSubtitle(e.target.checked)} />
              Nhúng subtitle vào video
            </label>
          </Field>
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14, gap: 8 }}>
          <Button>Save preset</Button>
          <Button variant="primary" disabled={submitting || !projectId} onClick={onRender}>
            {submitting ? "Đang khởi động…" : "Render Video"}
          </Button>
        </div>
        {error && (
          <div
            style={{
              marginTop: 10,
              background: "#450a0a",
              color: theme.danger,
              padding: 10,
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            {error}
          </div>
        )}
        {result && (
          <div
            style={{
              marginTop: 10,
              background: "#052e16",
              color: theme.success,
              padding: 10,
              borderRadius: 6,
              fontSize: 12,
            }}
          >
            Workflow started: {result}
          </div>
        )}
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}
