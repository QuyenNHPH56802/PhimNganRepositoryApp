"use client";

import { useEffect, useRef } from "react";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import { Button } from "@/components/ui";

interface VideoPlayerProps {
  src?: string;
  poster?: string;
}

export function VideoPlayer({ src, poster }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement>(null);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const durationMs = useEditor((s) => s.durationMs);
  const setTime = useEditor((s) => s.setTime);
  const setDuration = useEditor((s) => s.setDuration);
  const setPlaying = useEditor((s) => s.setPlaying);
  const playing = useEditor((s) => s.playing);
  const volume = useEditor((s) => s.volume);
  const setVolume = useEditor((s) => s.setVolume);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    if (Math.abs(v.currentTime * 1000 - currentTimeMs) > 150) {
      v.currentTime = currentTimeMs / 1000;
    }
  }, [currentTimeMs]);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    v.volume = volume;
  }, [volume]);

  function togglePlay() {
    const v = ref.current;
    if (!v) return;
    if (v.paused) {
      v.play().catch(() => {});
    } else {
      v.pause();
    }
  }

  function step(deltaMs: number) {
    const v = ref.current;
    if (!v) return;
    v.currentTime = Math.max(0, v.currentTime + deltaMs / 1000);
  }

  return (
    <div
      style={{
        position: "relative",
        background: "#000",
        borderRadius: 8,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        flex: 1,
      }}
    >
      <div style={{ flex: 1, position: "relative", minHeight: 0, display: "grid", placeItems: "center" }}>
        {src ? (
          <video
            ref={ref}
            src={src}
            poster={poster}
            style={{ width: "100%", maxHeight: "100%", display: "block" }}
            onTimeUpdate={(e) => setTime((e.target as HTMLVideoElement).currentTime * 1000)}
            onLoadedMetadata={(e) => setDuration((e.target as HTMLVideoElement).duration * 1000)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
          />
        ) : (
          <div style={{ color: theme.textMuted, fontSize: 13, padding: 32, textAlign: "center" }}>
            <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.5 }}>▷</div>
            <div>Chưa có video. Upload từ trang project hoặc kéo thả file vào đây.</div>
          </div>
        )}
      </div>
      <div
        style={{
          padding: "8px 12px",
          background: "#0d172e",
          borderTop: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <Button size="icon" onClick={() => step(-5000)} title="Lùi 5s">
          ⏪
        </Button>
        <Button size="icon" onClick={togglePlay} title={playing ? "Tạm dừng (Space)" : "Phát (Space)"}>
          {playing ? "⏸" : "▶"}
        </Button>
        <Button size="icon" onClick={() => step(5000)} title="Tiến 5s">
          ⏩
        </Button>
        <span style={{ fontSize: 12, fontVariantNumeric: "tabular-nums", color: theme.textMuted, minWidth: 100 }}>
          {fmt(currentTimeMs)} / {fmt(durationMs)}
        </span>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 11, color: theme.textMuted }}>Âm lượng</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={(e) => setVolume(parseFloat(e.target.value))}
          style={{ width: 100 }}
        />
      </div>
    </div>
  );
}

function fmt(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "00:00.0";
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  const t = Math.floor((ms % 1000) / 100);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${t}`;
}
