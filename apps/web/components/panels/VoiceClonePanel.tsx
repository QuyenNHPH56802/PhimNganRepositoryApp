"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, SkeletonPanel } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  createVoiceCloneSample,
  deleteVoiceCloneSample,
  listVoiceCloneSamples,
  runVoiceClone,
  type VoiceCloneSample,
} from "@/lib/voiceClone";

interface Props {
  projectId: string;
}

const PROVIDERS = [
  { id: "voice.mock", label: "Mock (dev)", desc: "Deterministic, GPU-free" },
  { id: "voice.xtts", label: "XTTS", desc: "High quality, requires GPU" },
];

export function VoiceClonePanel({ projectId }: Props) {
  const { toast } = useToast();
  const [samples, setSamples] = useState<VoiceCloneSample[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [label, setLabel] = useState("");
  const [storageKey, setStorageKey] = useState("");
  const [durationMs, setDurationMs] = useState(8000);
  const [providerId, setProviderId] = useState("voice.mock");
  const [submitting, setSubmitting] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listVoiceCloneSamples(projectId);
      setSamples(Array.isArray(list) ? list : []);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate() {
    if (!label.trim() || !storageKey.trim()) {
      toast("Cần nhập label và storage_key", "warn");
      return;
    }
    setSubmitting(true);
    try {
      await createVoiceCloneSample(projectId, {
        label: label.trim(),
        sample_storage_key: storageKey.trim(),
        provider_id: providerId,
        duration_ms: durationMs,
      });
      toast("Đã tạo sample", "success");
      setLabel("");
      setStorageKey("");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRun(s: VoiceCloneSample) {
    setRunningId(s.id);
    try {
      await runVoiceClone(projectId, s.id);
      toast(`Clone hoàn tất — quality ${s.quality_score?.toFixed(2) ?? "?"}`, "success");
      await refresh();
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast(msg, "danger");
      await refresh();
    } finally {
      setRunningId(null);
    }
  }

  async function handleDelete(s: VoiceCloneSample) {
    if (!window.confirm(`Xoá sample "${s.label}"?`)) return;
    try {
      await deleteVoiceCloneSample(projectId, s.id);
      toast("Đã xoá", "info");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  if (loading && samples === null) {
    return <SkeletonPanel title="Voice Cloning" rows={3} />;
  }

  return (
    <Card title="🎙️ Voice Cloning" padded={false}>
      {/* Form */}
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
          TẠO SAMPLE MỚI
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 100px", gap: 8 }}>
          <Input
            placeholder="Label (VD: MC giọng nữ)"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            disabled={submitting}
          />
          <Input
            placeholder="Storage key (VD: samples/mc_female.wav)"
            value={storageKey}
            onChange={(e) => setStorageKey(e.target.value)}
            disabled={submitting}
          />
          <Input
            type="number"
            min={1000}
            max={120000}
            step={500}
            value={durationMs}
            onChange={(e) => setDurationMs(parseInt(e.target.value || "8000", 10))}
            disabled={submitting}
            title="Duration in ms"
          />
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select
            value={providerId}
            onChange={(e) => setProviderId(e.target.value)}
            disabled={submitting}
            style={{
              background: theme.bgPanel,
              border: `1px solid ${theme.border}`,
              color: theme.text,
              padding: "6px 10px",
              borderRadius: 4,
              fontSize: 12,
              minWidth: 180,
            }}
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label} — {p.desc}
              </option>
            ))}
          </select>
          <Button variant="primary" onClick={handleCreate} disabled={submitting} size="sm">
            {submitting ? "…" : "+ Tạo sample"}
          </Button>
          <span style={{ marginLeft: "auto", fontSize: 10, color: theme.textDim }}>
            Sau khi tạo → nhấn ▶ Run để bắt đầu clone
          </span>
        </div>
      </div>

      {/* List */}
      {!samples || samples.length === 0 ? (
        <EmptyState
          title="Chưa có sample nào"
          description="Upload audio (>= 6 giây) qua /storage API, paste storage key vào form trên."
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column" }}>
          {samples.map((s) => (
            <SampleRow
              key={s.id}
              sample={s}
              running={runningId === s.id}
              onRun={() => handleRun(s)}
              onDelete={() => handleDelete(s)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function SampleRow({
  sample,
  running,
  onRun,
  onDelete,
}: {
  sample: VoiceCloneSample;
  running: boolean;
  onRun: () => void;
  onDelete: () => void;
}) {
  const statusColor: Record<string, string> = {
    queued: theme.textMuted,
    running: theme.accent,
    completed: theme.success,
    failed: theme.danger,
  };
  const c = statusColor[sample.status] ?? theme.text;

  return (
    <div
      style={{
        padding: 14,
        borderBottom: `1px solid ${theme.border}`,
        display: "grid",
        gridTemplateColumns: "1fr 200px 100px 120px",
        gap: 12,
        alignItems: "center",
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: 14 }}>{sample.label}</div>
        <div
          style={{
            fontSize: 10,
            color: theme.textMuted,
            fontFamily: "ui-monospace",
            marginTop: 4,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={sample.sample_storage_key}
        >
          {sample.sample_storage_key}
        </div>
        <audio
          controls
          preload="none"
          src={sample.sample_download_url}
          style={{ width: "100%", marginTop: 6, height: 28 }}
        />
        {sample.preview_download_url && (
          <div style={{ marginTop: 6 }}>
            <span style={{ fontSize: 10, color: theme.success, fontWeight: 700 }}>
              Preview:
            </span>
            <audio
              controls
              preload="none"
              src={sample.preview_download_url}
              style={{ width: "100%", marginTop: 4, height: 28 }}
            />
          </div>
        )}
        {sample.error_message && (
          <div
            style={{
              fontSize: 11,
              color: theme.danger,
              marginTop: 4,
              padding: "2px 6px",
              background: `${theme.danger}11`,
              borderRadius: 3,
            }}
          >
            ⚠ {sample.error_message}
          </div>
        )}
      </div>

      <div style={{ fontSize: 11, color: theme.textMuted }}>
        <div>Provider: {sample.provider_id}</div>
        <div>Duration: {(sample.duration_ms / 1000).toFixed(2)}s</div>
        {sample.quality_score !== null && (
          <div>
            Quality:{" "}
            <strong style={{ color: sample.quality_score >= 0.7 ? theme.success : theme.warn }}>
              {sample.quality_score.toFixed(2)}
            </strong>
          </div>
        )}
      </div>

      <div
        style={{
          fontSize: 11,
          padding: "4px 8px",
          background: `${c}22`,
          color: c,
          borderRadius: 4,
          fontWeight: 700,
          textTransform: "uppercase",
          textAlign: "center",
        }}
      >
        {sample.status}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <Button
          size="sm"
          variant="primary"
          onClick={onRun}
          disabled={running || sample.status === "running"}
        >
          {running ? "⏳ Cloning…" : sample.status === "completed" ? "↻ Re-run" : "▶ Run"}
        </Button>
        <Button size="sm" variant="danger" onClick={onDelete}>
          Xoá
        </Button>
      </div>
    </div>
  );
}
