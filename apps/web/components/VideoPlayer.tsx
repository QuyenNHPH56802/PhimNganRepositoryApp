"use client";

import { useEffect, useRef, useState } from "react";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import { Button } from "@/components/ui";
import { useAudioMixer } from "@/lib/useAudioMixer";

interface VideoPlayerProps {
  src?: string;
  poster?: string;
}

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

export function VideoPlayer({ src, poster }: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const speedMenuRef = useRef<HTMLDivElement>(null);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const durationMs = useEditor((s) => s.durationMs);
  const setTime = useEditor((s) => s.setTime);
  const setDuration = useEditor((s) => s.setDuration);
  const setPlaying = useEditor((s) => s.setPlaying);
  const playing = useEditor((s) => s.playing);
  const volume = useEditor((s) => s.volume);
  const setVolume = useEditor((s) => s.setVolume);
  const audioMixGains = useEditor((s) => s.audioMixGains);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);

  // Initialize Web Audio API for real-time mixing
  const { initialized: audioMixerInitialized } = useAudioMixer({
    videoRef: ref,
    gains: audioMixGains,
    enabled: true,
  });

  // Determine the actual video source
  const videoSrc = (() => {
    if (!src) return null;
    
    // If it's already a full URL (e.g., from external source), use it directly
    if (src.startsWith("http://") || src.startsWith("https://")) {
      return src;
    }
    
    // If it's a local asset path from backend, proxy it
    if (src.startsWith("/local-assets/")) {
      return `/api/proxy-video?path=${encodeURIComponent(src)}`;
    }
    
    // If it's a public folder path (starts with /), use it directly
    if (src.startsWith("/") && !src.startsWith("/api/")) {
      return src;
    }
    
    return src;
  })();

  useEffect(() => {
    const v = ref.current;
    if (!v || !Number.isFinite(v.duration)) return;
    // Only sync to currentTimeMs when the user clicked the scrub bar (a big
    // jump). onTimeUpdate already keeps the store in sync, so the only times
    // currentTimeMs and v.currentTime drift apart by more than 150ms is when
    // the store was changed by a click handler.
    const driftMs = Math.abs(v.currentTime * 1000 - (currentTimeMs ?? 0));
    if (driftMs > 250) {
      v.currentTime = (currentTimeMs ?? 0) / 1000;
    }
  }, [currentTimeMs]);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    v.volume = volume;
  }, [volume]);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    v.playbackRate = playbackRate;
  }, [playbackRate]);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      const el = ref.current;
      if (!el) return;
      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        if (el.paused) el.play().catch(() => {});
        else el.pause();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        el.currentTime = Math.max(0, el.currentTime - 5);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        el.currentTime = el.currentTime + 5;
      } else if (e.key === "Home") {
        e.preventDefault();
        el.currentTime = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        el.currentTime = el.duration || 0;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    function handleFullscreenChange() {
      setIsFullscreen(!!document.fullscreenElement);
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // Close the speed menu on outside click so it doesn't linger over the controls.
  useEffect(() => {
    if (!showSpeedMenu) return;
    function onDown(e: MouseEvent) {
      if (speedMenuRef.current && !speedMenuRef.current.contains(e.target as Node)) {
        setShowSpeedMenu(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setShowSpeedMenu(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [showSpeedMenu]);

  function togglePlay() {
    const v = ref.current;
    if (!v) return;
    if (v.paused) {
      const p = v.play();
      if (p && typeof p.catch === "function") {
        p.catch(() => {});
      }
    } else {
      v.pause();
    }
  }

  function step(deltaMs: number) {
    const v = ref.current;
    if (!v) return;
    v.currentTime = Math.max(0, v.currentTime + deltaMs / 1000);
  }

  function onProgressClick(e: React.MouseEvent) {
    const v = ref.current;
    const bar = progressRef.current;
    if (!v || !bar) return;
    const rect = bar.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const newTime = ratio * v.duration;
    v.currentTime = newTime;
    setTime(newTime * 1000);
  }

  function toggleFullscreen() {
    const el = containerRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      el.requestFullscreen();
    }
  }

  const progress = durationMs > 0 ? (currentTimeMs / durationMs) * 100 : 0;

  return (
    <div
      ref={containerRef}
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
      <div style={{ flex: 1, position: "relative", minHeight: 0, minWidth: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "#000" }}>
        {videoSrc ? (
          <video
            key={`${src ?? "empty"}`}
            ref={ref}
            src={videoSrc}
            poster={poster}
            preload="metadata"
            playsInline
            style={{ width: "100%", height: "100%", maxHeight: "100%", objectFit: "contain", display: "block" }}
            onTimeUpdate={(e) => {
              const ms = (e.target as HTMLVideoElement).currentTime * 1000;
              if (Math.abs(ms - currentTimeMs) > 50) setTime(ms);
            }}
            onLoadedMetadata={(e) => setDuration((e.target as HTMLVideoElement).duration * 1000)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
            onWaiting={() => setVideoError(null)}
            onError={() => setVideoError("Failed to load video — check console for details")}
            onCanPlay={() => setVideoError(null)}
          />
        ) : null}
        
        {!videoSrc && (
          <div style={{ color: theme.textMuted, fontSize: 13, padding: 32, textAlign: "center" }}>
            <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.5 }}>▷</div>
            <div>Chưa có video. Upload từ trang project hoặc kéo thả file vào đây.</div>
          </div>
        )}
        
        {videoSrc && videoError && (
          <div style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(0,0,0,0.85)",
            color: theme.textMuted,
            padding: 32,
            textAlign: "center",
            gap: 12
          }}>
            <div style={{ fontSize: 48, marginBottom: 4 }}>⚠️</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: theme.text }}>Không thể tải video</div>
            <div style={{ fontSize: 12 }}>{videoError}</div>
            <div style={{ fontSize: 10, color: theme.textDim, marginTop: 4, wordBreak: "break-all", maxWidth: 400 }}>
              {src}
            </div>
            <Button
              size="sm"
              variant="primary"
              onClick={() => { setVideoError(null); if (ref.current) { ref.current.load(); } }}
              style={{ marginTop: 8 }}
            >
              🔄 Thử lại
            </Button>
          </div>
        )}

        {videoSrc && !videoError && !playing && durationMs > 0 && (
          <button
            onClick={togglePlay}
            aria-label="Phát"
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              width: 72,
              height: 72,
              borderRadius: "50%",
              border: "none",
              background: "rgba(0,0,0,0.55)",
              color: "#fff",
              fontSize: 32,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              paddingLeft: 6,
            }}
          >
            ▶
          </button>
        )}
      </div>
      <div
        style={{
          padding: "8px 12px",
          background: "#0d172e",
          borderTop: `1px solid ${theme.border}`,
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        <div
          ref={progressRef}
          onClick={onProgressClick}
          onMouseMove={(e) => {
            const thumb = e.currentTarget.querySelector('[data-role="progress-thumb"]') as HTMLElement | null;
            if (thumb) thumb.style.opacity = "1";
          }}
          onMouseLeave={(e) => {
            const thumb = e.currentTarget.querySelector('[data-role="progress-thumb"]') as HTMLElement | null;
            if (thumb) thumb.style.opacity = "0";
          }}
          style={{
            height: 6,
            background: theme.bgPanel,
            borderRadius: 3,
            cursor: "pointer",
            position: "relative",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progress}%`,
              background: theme.accent,
              borderRadius: 2,
              transition: "width 100ms linear",
            }}
          />
          <div
            data-role="progress-thumb"
            style={{
              position: "absolute",
              top: "50%",
              left: `${progress}%`,
              transform: "translate(-50%, -50%)",
              width: 12,
              height: 12,
              background: theme.accent,
              borderRadius: "50%",
              boxShadow: `0 0 6px ${theme.accent}`,
              opacity: 0,
              transition: "opacity 150ms",
              pointerEvents: "none",
            }}
          />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Button size="icon" onClick={() => step(-5000)} title="Lùi 5s (←)" aria-label="Lùi 5 giây">
            ⏪
          </Button>
          <Button
            size="icon"
            variant="primary"
            onClick={togglePlay}
            disabled={!videoSrc || durationMs <= 0}
            title={playing ? "Tạm dừng (Space)" : "Phát (Space)"}
            aria-label={playing ? "Tạm d�ng" : "Phát"}
            style={{ width: 40, height: 40, fontSize: 16, fontWeight: 700 }}
          >
            {playing ? "⏸" : "▶"}
          </Button>
          <Button size="icon" onClick={() => step(5000)} title="Tiến 5s (→)" aria-label="Tiến 5 giây">
            ⏩
          </Button>
          <span style={{ fontSize: 12, fontVariantNumeric: "tabular-nums", color: theme.textMuted, minWidth: 100 }}>
            {fmt(currentTimeMs)} / {fmt(durationMs)}
          </span>
          <div style={{ flex: 1 }} />
          <div ref={speedMenuRef} style={{ position: "relative" }}>
            <Button size="sm" variant="ghost" onClick={() => setShowSpeedMenu(!showSpeedMenu)} title="Tốc độ phát" aria-haspopup="menu" aria-expanded={showSpeedMenu}>
              {playbackRate}x
            </Button>
            {showSpeedMenu && (
              <div
                role="menu"
                style={{
                  position: "absolute",
                  bottom: "100%",
                  right: 0,
                  marginBottom: 4,
                  background: theme.bgElevated,
                  border: `1px solid ${theme.border}`,
                  borderRadius: 6,
                  overflow: "hidden",
                  zIndex: 10,
                }}
              >
                {SPEEDS.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setPlaybackRate(s); setShowSpeedMenu(false); }}
                    style={{
                      display: "block",
                      width: "100%",
                      padding: "6px 14px",
                      background: playbackRate === s ? "rgba(125,211,252,0.12)" : "transparent",
                      color: playbackRate === s ? theme.accent : theme.text,
                      border: "none",
                      fontSize: 12,
                      fontWeight: playbackRate === s ? 600 : 400,
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            )}
          </div>
          <span style={{ fontSize: 11, color: theme.textMuted }}>Âm lượng</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            style={{ width: 80 }}
          />
          <Button size="icon" onClick={toggleFullscreen} title={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}>
            {isFullscreen ? "⊠" : "⛶"}
          </Button>
        </div>
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
