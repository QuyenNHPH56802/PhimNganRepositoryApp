"use client";

import { useEffect, useMemo, useRef } from "react";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import type { SubtitleSegment, TranscriptSegment } from "@/lib/types";

const TRACK_HEIGHT = 36;
const SUBTITLE_TRACK_HEIGHT = 56;

export function Timeline({ videoSrc }: { videoSrc?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const durationMs = useEditor((s) => s.durationMs);
  const currentTimeMs = useEditor((s) => s.currentTimeMs);
  const setTime = useEditor((s) => s.setTime);
  const zoom = useEditor((s) => s.zoom);
  const setZoom = useEditor((s) => s.setZoom);
  const transcript = useEditor((s) => s.transcript);
  const subtitles = useEditor((s) => s.subtitles);
  const audio = useEditor((s) => s.audio);
  const selectedSegmentId = useEditor((s) => s.selectedSegmentId);
  const selectSegment = useEditor((s) => s.selectSegment);
  const splitSubtitle = useEditor((s) => s.splitSubtitle);

  const totalMs = durationMs > 0 ? durationMs : 60_000;
  const pxPerMs = (zoom / 100) * 0.1;
  const width = Math.max(800, totalMs * pxPerMs);

  function pxToMs(px: number): number {
    return Math.max(0, Math.min(totalMs, px / pxPerMs));
  }

  function onRulerClick(e: React.MouseEvent) {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + containerRef.current.scrollLeft;
    setTime(pxToMs(x));
  }

  const ticks = useMemo(() => {
    const target = 100;
    const rawStep = target / pxPerMs;
    const steps = [100, 250, 500, 1000, 2000, 5000, 10_000, 30_000, 60_000];
    const step = steps.find((s) => s >= rawStep) ?? 60_000;
    const count = Math.ceil(totalMs / step) + 1;
    return Array.from({ length: count }, (_, i) => ({ ms: i * step, label: fmt(i * step) }));
  }, [totalMs, pxPerMs]);

  return (
    <div
      style={{
        background: "#0d172e",
        borderTop: `1px solid ${theme.border}`,
        display: "flex",
        flexDirection: "column",
        minHeight: 220,
      }}
    >
      <div
        style={{
          padding: "6px 12px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 11,
          color: theme.textMuted,
        }}
      >
        <span>Timeline</span>
        <span>Zoom</span>
        <input
          type="range"
          min={20}
          max={400}
          value={zoom}
          onChange={(e) => setZoom(parseInt(e.target.value, 10))}
        />
        <span>{zoom}%</span>
        <span style={{ marginLeft: "auto" }}>
          {subtitles?.length ?? 0} phụ đề • {transcript?.length ?? 0} bản ghi • {audio?.length ?? 0} âm thanh
        </span>
      </div>

      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflowX: "auto",
          overflowY: "hidden",
          position: "relative",
        }}
      >
        <div style={{ width, position: "relative" }}>
          <div
            onClick={onRulerClick}
            style={{
              position: "sticky",
              top: 0,
              height: 28,
              background: "#0a1426",
              borderBottom: `1px solid ${theme.border}`,
              cursor: "pointer",
              zIndex: 3,
              userSelect: "none",
            }}
          >
            {ticks.map((t) => (
              <div
                key={t.ms}
                style={{
                  position: "absolute",
                  left: t.ms * pxPerMs,
                  top: 0,
                  height: "100%",
                  borderLeft: `1px solid ${theme.borderStrong}`,
                  fontSize: 10,
                  color: theme.textDim,
                  paddingLeft: 4,
                }}
              >
                {t.label}
              </div>
            ))}
          </div>

          <Track
            label="Video (ZH)"
            height={TRACK_HEIGHT}
            width={width}
            segments={(transcript ?? []).map((t: any) => {
              const textContent = t.text || t.raw_text || t.normalized_text || "";
              return {
                id: t.id,
                startMs: t.start_ms ?? 0,
                endMs: t.end_ms ?? 0,
                label: textContent.slice(0, 30),
                color: theme.bgPanel,
              };
            })}
            pxPerMs={pxPerMs}
            onSeek={(ms) => setTime(ms)}
          />

          <SubtitleTrack
            width={width}
            segments={subtitles ?? []}
            pxPerMs={pxPerMs}
            selectedId={selectedSegmentId}
            onSelect={selectSegment}
            onSplit={(id, atMs) => splitSubtitle(id, atMs)}
            onSeek={(ms) => setTime(ms)}
          />

          <Track
            label="Voice (VI)"
            height={TRACK_HEIGHT}
            width={width}
            segments={(audio ?? []).map((a) => ({
              id: a.id,
              startMs: a.start_ms ?? 0,
              endMs: (a.start_ms ?? 0) + (a.duration_ms ?? 0),
              label: "",
              color: theme.speaker1,
            }))}
            pxPerMs={pxPerMs}
            onSeek={(ms) => setTime(ms)}
          />

          <Playhead width={width} currentTimeMs={currentTimeMs} pxPerMs={pxPerMs} />
        </div>
      </div>
    </div>
  );
}

interface TrackSegment {
  id: string;
  startMs: number;
  endMs: number;
  label: string;
  color: string;
}

function Track({
  label,
  height,
  width,
  segments,
  pxPerMs,
  onSeek,
}: {
  label: string;
  height: number;
  width: number;
  segments: TrackSegment[];
  pxPerMs: number;
  onSeek: (ms: number) => void;
}) {
  return (
    <div
      style={{
        position: "relative",
        height,
        borderBottom: `1px solid ${theme.border}`,
        background: "#0b1424",
      }}
    >
      <div
        style={{
          position: "sticky",
          left: 0,
          top: 0,
          zIndex: 2,
          width: 80,
          height: "100%",
          background: "rgba(13,23,46,0.9)",
          borderRight: `1px solid ${theme.border}`,
          padding: "0 8px",
          display: "flex",
          alignItems: "center",
          fontSize: 11,
          color: theme.textMuted,
        }}
      >
        {label}
      </div>
      {segments.map((seg) => (
        <div
          key={seg.id}
          onClick={() => onSeek(seg.startMs)}
          style={{
            position: "absolute",
            left: Math.max(80, seg.startMs * pxPerMs),
            top: 6,
            height: height - 12,
            width: Math.max(2, (seg.endMs - seg.startMs) * pxPerMs),
            background: seg.color,
            border: `1px solid ${theme.borderStrong}`,
            borderRadius: 3,
            overflow: "hidden",
            fontSize: 10,
            padding: "0 4px",
            color: theme.text,
            whiteSpace: "nowrap",
            cursor: "pointer",
          }}
          title={seg.label}
        >
          {seg.label}
        </div>
      ))}
    </div>
  );
}

function SubtitleTrack({
  width,
  segments,
  pxPerMs,
  selectedId,
  onSelect,
  onSplit,
  onSeek,
}: {
  width: number;
  segments: SubtitleSegment[];
  pxPerMs: number;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onSplit: (id: string, atMs: number) => void;
  onSeek: (ms: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  function onDoubleClick(e: React.MouseEvent, seg: SubtitleSegment) {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const atMs = seg.start_ms + x / pxPerMs;
    onSplit(seg.id, atMs);
  }

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        height: SUBTITLE_TRACK_HEIGHT,
        borderBottom: `1px solid ${theme.border}`,
        background: "#0e1a30",
      }}
    >
      <div
        style={{
          position: "sticky",
          left: 0,
          top: 0,
          zIndex: 2,
          width: 80,
          height: "100%",
          background: "rgba(14,26,48,0.9)",
          borderRight: `1px solid ${theme.border}`,
          padding: "0 8px",
          display: "flex",
          alignItems: "center",
          fontSize: 11,
          color: theme.accent,
        }}
      >
        Subtitle
      </div>
      {segments.map((seg: any) => {
        const textContent = seg.text || seg.display_text || "";
        const left = Math.max(80, (seg.start_ms ?? 0) * pxPerMs);
        const w = Math.max(40, ((seg.end_ms ?? 0) - (seg.start_ms ?? 0)) * pxPerMs);
        return (
          <div
            key={seg.id}
            onClick={(e) => {
              e.stopPropagation();
              onSelect(seg.id);
            }}
            onDoubleClick={(e) => onDoubleClick(e, seg)}
            style={{
              position: "absolute",
              left,
              top: 6,
              width: w,
              height: SUBTITLE_TRACK_HEIGHT - 12,
              background: selectedId === seg.id ? "rgba(125,211,252,0.25)" : "rgba(125,211,252,0.10)",
              border: `1px solid ${selectedId === seg.id ? theme.accent : "#1d4a6e"}`,
              borderRadius: 4,
              padding: "2px 6px",
              fontSize: 11,
              color: theme.text,
              overflow: "hidden",
              cursor: "pointer",
              whiteSpace: "nowrap",
              textOverflow: "ellipsis",
            }}
            title={`${fmt(seg.start_ms ?? 0)} → ${fmt(seg.end_ms ?? 0)}: ${textContent}`}
          >
            {textContent}
          </div>
        );
      })}
    </div>
  );
}

function Playhead({
  width,
  currentTimeMs,
  pxPerMs,
}: {
  width: number;
  currentTimeMs: number;
  pxPerMs: number;
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: (currentTimeMs ?? 0) * pxPerMs,
        height: "100%",
        width: 2,
        background: theme.danger,
        zIndex: 5,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: -5,
          width: 12,
          height: 12,
          background: theme.danger,
          transform: "rotate(45deg)",
          transformOrigin: "center",
        }}
      />
    </div>
  );
}

function fmt(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "00:00";
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
