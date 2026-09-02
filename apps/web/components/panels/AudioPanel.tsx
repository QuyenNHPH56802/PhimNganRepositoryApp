"use client";

import { useEffect, useState } from "react";
import { Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";

const tracks = [
  { id: "original", label: "Original (ZH)", color: theme.speaker1 },
  { id: "voice_vi", label: "Voice (VI)", color: theme.speaker2 },
  { id: "music", label: "Music", color: theme.speaker3 },
  { id: "sfx", label: "SFX", color: theme.speaker4 },
];

const DEFAULT_GAINS: Record<string, number> = { original: 1, voice_vi: 1, music: 0.5, sfx: 0.7 };
const GAINS_KEY = "translator_audio_gains";

export function AudioPanel() {
  const [muted, setMuted] = useState<Record<string, boolean>>({});
  const [solo, setSolo] = useState<Record<string, boolean>>({});
  const [gains, setGains] = useState<Record<string, number>>(() => {
    if (typeof window === "undefined") return DEFAULT_GAINS;
    try {
      const raw = window.localStorage.getItem(GAINS_KEY);
      return raw ? JSON.parse(raw) : DEFAULT_GAINS;
    } catch {
      return DEFAULT_GAINS;
    }
  });
  const projectId = useEditor((s) => s.projectId);
  const [processing, setProcessing] = useState(false);
  const { toast } = useToast();

  // Persist gain changes so they survive reloads.
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(GAINS_KEY, JSON.stringify(gains));
  }, [gains]);

  function toggleMute(id: string) {
    setMuted((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function toggleSolo(id: string) {
    setSolo((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      // If any track is soloed, all non-soloed tracks are effectively muted.
      const anySolo = Object.values(next).some(Boolean);
      if (anySolo) {
        const mutedFromSolo: Record<string, boolean> = {};
        for (const t of tracks) mutedFromSolo[t.id] = !next[t.id];
        setMuted((prevMuted) => ({ ...prevMuted, ...mutedFromSolo }));
      } else {
        // Turning off the last solo clears the implicit mutes.
        setMuted({});
      }
      return next;
    });
  }

  function formatGain(g: number): string {
    if (g === 0) return "-∞";
    const db = 20 * Math.log10(g);
    return `${db >= 0 ? "+" : ""}${db.toFixed(1)} dB`;
  }

  async function handleAutoMix() {
    if (!projectId) {
      toast("Vui lòng chọn project trước", "warn");
      return;
    }
    setProcessing(true);
    try {
      const result = await api.autoMixAudio(projectId, gains);
      if (result?.gains) {
        setGains(result.gains);
        toast("Đã cân bằng mix tự động", "success");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast(`Cân bằng thất bại: ${msg}`, "danger");
    } finally {
      setProcessing(false);
    }
  }

  async function handleRenderMix() {
    if (!projectId) {
      toast("Vui lòng chọn project trước", "warn");
      return;
    }
    setProcessing(true);
    try {
      const result = await api.renderAudioMix(projectId, gains);
      if (result?.audio_url) {
        window.open(result.audio_url, "_blank");
        toast("Đã render mix, đang mở audio…", "success");
      } else {
        toast("Render mix không trả về audio_url", "warn");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast(`Render mix thất bại: ${msg}`, "danger");
    } finally {
      setProcessing(false);
    }
  }

  async function handlePreviewMix() {
    // Quick preview uses the same render endpoint; surfaces the result inline.
    await handleRenderMix();
  }

  function handleResetGains() {
    setGains({ ...DEFAULT_GAINS });
    setMuted({});
    setSolo({});
  }

  return (
    <Card padded={false}>
      <div
        style={{
          padding: "10px 12px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "#0d172e",
        }}
      >
        <strong style={{ fontSize: 13 }}>Audio Mix</strong>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <Button
            size="sm"
            variant="ghost"
            disabled={processing}
            onClick={handleResetGains}
          >
            ↺ Reset
          </Button>
          <Button
            size="sm"
            disabled={processing}
            onClick={handleAutoMix}
          >
            {processing ? "..." : "⚖️"} Cân bằng tự động
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={processing}
            onClick={handlePreviewMix}
            title="Render mix hiện tại rồi mở audio để nghe"
          >
            {processing ? "..." : "🎧"} Nghe thử
          </Button>
          <Button
            size="sm"
            variant="primary"
            disabled={processing}
            onClick={handleRenderMix}
          >
            {processing ? "..." : "🎵"} Render mix
          </Button>
        </div>
      </div>
      
      {tracks.map((t) => {
        const isMuted = muted[t.id];
        const isSolo = solo[t.id];
        const gain = isMuted ? 0 : gains[t.id] ?? 1;
        
        return (
          <div
            key={t.id}
            style={{
              padding: "12px",
              borderBottom: `1px solid ${theme.border}`,
              display: "grid",
              gridTemplateColumns: "120px 80px 1fr 70px",
              gap: 12,
              alignItems: "center",
              opacity: isMuted ? 0.5 : 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 10, height: 10, borderRadius: 999, background: t.color }} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{t.label}</span>
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              <Button
                size="sm"
                variant={isMuted ? "primary" : "default"}
                title="Tắt tiếng"
                onClick={() => toggleMute(t.id)}
              >
                M
              </Button>
              <Button
                size="sm"
                variant={isSolo ? "primary" : "default"}
                title="Chỉ nghe kênh này"
                onClick={() => toggleSolo(t.id)}
              >
                S
              </Button>
            </div>
            <input
              type="range"
              min={0}
              max={1.5}
              step={0.01}
              value={gain}
              onChange={(e) => setGains((prev) => ({ ...prev, [t.id]: parseFloat(e.target.value) }))}
              style={{ width: "100%" }}
              disabled={isMuted}
            />
            <span style={{ fontSize: 11, color: theme.textMuted, textAlign: "right" }}>
              {formatGain(gain)}
            </span>
          </div>
        );
      })}
      
      <div style={{ padding: 12, background: theme.bgPanel }}>
        <div style={{ fontSize: 11, color: theme.textMuted, marginBottom: 8 }}>
          Mẹo: Nhấn M để tắt tiếng, S để chỉ nghe kênh đó
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button size="sm" variant="ghost" onClick={() => setGains((p) => ({ ...p, voice_vi: 1.2 }))}>
            Tăng voice +20%
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setGains((p) => ({ ...p, music: 0.3 }))}>
            Giảm nhạc -50%
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setGains({ original: 0, voice_vi: 1, music: 0, sfx: 0 })}>
            Chỉ voice VI
          </Button>
        </div>
      </div>
    </Card>
  );
}
