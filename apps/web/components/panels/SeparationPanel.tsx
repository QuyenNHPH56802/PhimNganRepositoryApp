"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, EmptyState, SkeletonPanel, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  deleteSeparationTrack,
  listSeparationTracks,
  runSeparation,
  type SeparationTrack,
} from "@/lib/separation";

interface Props {
  projectId: string;
}

const KIND_META: Record<string, { label: string; emoji: string; color: string }> = {
  vocals: { label: "Giọng hát riêng", emoji: "🎤", color: "#60a5fa" },
  background: { label: "Nhạc nền + SFX", emoji: "🎵", color: "#a78bfa" },
  // legacy kinds from previous runs
  music: { label: "Nhạc nền", emoji: "🎵", color: "#a78bfa" },
  sfx: { label: "Hiệu ứng", emoji: "💥", color: "#f97316" },
  instrumental: { label: "Instrumental", emoji: "🎼", color: "#10b981" },
};

const METHODS = [
  { id: "MDX23K", label: "MDX23K (UVR5 MDX)", desc: "Cân bằng chất lượng / tốc độ" },
  { id: "Demucs", label: "Demucs", desc: "Chất lượng cao, chậm hơn" },
  { id: "BS-RoFormer", label: "BS-RoFormer", desc: "Chất lượng tốt nhất, chậm nhất" },
];

export function SeparationPanel({ projectId }: Props) {
  const { toast } = useToast();
  const [tracks, setTracks] = useState<SeparationTrack[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [method, setMethod] = useState("MDX23K");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listSeparationTracks(projectId);
      setTracks(Array.isArray(r) ? r : []);
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
    setRunning(true);
    try {
      const result = await runSeparation(projectId, {
        provider_id: "separation.mock",
        method,
      });
      toast(`Đã tách ${result.tracks.length} track (${result.method})`, "success");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setRunning(false);
    }
  }

  async function handleDelete(t: SeparationTrack) {
    if (!window.confirm(`Xoá track ${t.kind}?`)) return;
    try {
      await deleteSeparationTrack(projectId, t.id);
      setTracks((prev) => prev?.filter((x) => x.id !== t.id) ?? null);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  if (loading && tracks === null) {
    return <SkeletonPanel title="Audio Separation" rows={3} />;
  }

  const tracksByKind = new Map<string, SeparationTrack[]>();
  tracks?.forEach((t) => {
    const existing = tracksByKind.get(t.kind) ?? [];
    existing.push(t);
    tracksByKind.set(t.kind, existing);
  });

  return (
    <Card
      title="🎵 Audio Separation"
      padded={false}
      action={
        <Button size="sm" variant="primary" onClick={handleRun} disabled={running}>
          {running ? "⏳ Đang tách…" : "▶ Tách audio"}
        </Button>
      }
    >
      <div
        style={{
          padding: 14,
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div>
          <div style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600, marginBottom: 6 }}>
            Phương pháp
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {METHODS.map((m) => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                style={{
                  padding: "8px 12px",
                  borderRadius: 6,
                  border: `1px solid ${method === m.id ? theme.accentStrong : theme.border}`,
                  background: method === m.id ? "rgba(125,211,252,0.08)" : theme.bgPanel,
                  color: method === m.id ? theme.text : theme.textMuted,
                  fontSize: 12,
                  fontWeight: 600,
                  textAlign: "left",
                  cursor: "pointer",
                  minWidth: 180,
                }}
              >
                <div>{m.label}</div>
                <div style={{ fontSize: 10, color: theme.textDim, marginTop: 2, fontWeight: 400 }}>
                  {m.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        {!tracks || tracks.length === 0 ? (
          <EmptyState
            title="Chưa có track được tách"
            description="Nhấn 'Tách audio' để chạy separation. Mock provider sẽ tạo placeholder tracks để demo UI."
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 10 }}>
            {tracks.map((t) => {
              const meta = KIND_META[t.kind] ?? {
                label: t.kind,
                emoji: "🎧",
                color: theme.textMuted,
              };
              return (
                <div
                  key={t.id}
                  style={{
                    padding: 12,
                    border: `1px solid ${theme.border}`,
                    borderRadius: 6,
                    background: theme.bgElevated,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 18 }}>{meta.emoji}</span>
                      <strong style={{ fontSize: 14, color: meta.color }}>{meta.label}</strong>
                    </div>
                    <span
                      style={{
                        fontSize: 10,
                        color: theme.textMuted,
                        fontFamily: "ui-monospace",
                        background: theme.bgPanel,
                        padding: "2px 6px",
                        borderRadius: 3,
                      }}
                    >
                      {(t.duration_ms / 1000).toFixed(2)}s
                    </span>
                  </div>

                  <div style={{ fontSize: 11, color: theme.textMuted, fontFamily: "ui-monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={t.storage_key}>
                    {t.storage_key}
                  </div>

                  <audio
                    controls
                    preload="none"
                    src={t.download_url}
                    style={{ width: "100%", height: 32 }}
                  />

                  <div style={{ display: "flex", gap: 6, justifyContent: "space-between", alignItems: "center" }}>
                    <a
                      href={t.download_url}
                      download
                      style={{
                        fontSize: 11,
                        color: theme.accent,
                        textDecoration: "none",
                      }}
                    >
                      ⬇ Download
                    </a>
                    <button
                      onClick={() => handleDelete(t)}
                      style={{
                        background: "transparent",
                        border: `1px solid ${theme.border}`,
                        color: theme.danger,
                        padding: "2px 8px",
                        borderRadius: 4,
                        cursor: "pointer",
                        fontSize: 11,
                      }}
                    >
                      Xoá
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
}
