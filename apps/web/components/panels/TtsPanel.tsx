"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button, Card, EmptyState, Select, SkeletonPanel } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import { humanizeError } from "@/lib/errorMessage";
import { useToast } from "@/lib/toast";
import type { AudioSegment, TranslationSegment } from "@/lib/types";

const VOICE_ASSIGNMENTS_KEY = "translator_voice_assignments";

function loadVoiceAssignments(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(VOICE_ASSIGNMENTS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveVoiceAssignments(assignments: Record<string, string>): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(VOICE_ASSIGNMENTS_KEY, JSON.stringify(assignments));
}

// Merge incoming audio segments with existing ones, deduplicating by id.
function mergeAudioSegments(existing: AudioSegment[], incoming: AudioSegment[]): AudioSegment[] {
  const byId = new Map<string, AudioSegment>();
  for (const a of existing) byId.set(a.id, a);
  for (const a of incoming) byId.set(a.id, a);
  return Array.from(byId.values());
}

export function TtsPanel() {
  const toast = useToast();
  const translation = useEditor((s) => s.translation);
  const voices = useEditor((s) => s.voices);
  const speakers = useEditor((s) => s.speakers);
  const audio = useEditor((s) => s.audio);
  const isInitialLoading = useEditor((s) => s.isInitialLoading);
  const loadAudio = useEditor((s) => s.loadAudio);
  const setTime = useEditor((s) => s.setTime);
  const projectId = useEditor((s) => s.projectId);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [generatingIds, setGeneratingIds] = useState<Set<string>>(new Set());
  const [previewingId, setPreviewingId] = useState<string | null>(null);
  const [voiceAssignments, setVoiceAssignments] = useState<Record<string, string>>(() => loadVoiceAssignments());

  // Persist voiceAssignments whenever they change.
  useEffect(() => {
    saveVoiceAssignments(voiceAssignments);
  }, [voiceAssignments]);

  if (isInitialLoading && translation.length === 0) {
    return <SkeletonPanel title="Tổng hợp giọng nói" rows={4} />;
  }

  if (translation.length === 0) {
    return (
      <EmptyState
        title="Chưa có segment để tổng hợp"
        description="Hoàn thành bước Translation trước."
      />
    );
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function getVoiceForSegment(segment: TranslationSegment): string | undefined {
    const speaker = speakers.find((s) => s.id === segment.speaker_id);
    return speaker?.voice_profile_id ?? voiceAssignments[segment.id];
  }

  function getAudioForSegment(segmentId: string) {
    return audio.find((a) => a.translation_segment_id === segmentId);
  }

  async function generateForSelected() {
    if (!projectId || selectedIds.size === 0) return;
    setGenerating(true);
    try {
      const ids = Array.from(selectedIds);
      // Group segment ids by their assigned voice so each request produces the
      // correct timbre for its segments.
      const grouped = new Map<string, string[]>();
      for (const id of ids) {
        const seg = translation.find((t) => t.id === id);
        if (!seg) continue;
        const voiceId = getVoiceForSegment(seg) ?? "";
        const bucket = grouped.get(voiceId) ?? [];
        bucket.push(id);
        grouped.set(voiceId, bucket);
      }
      const merged: AudioSegment[] = [];
      for (const [voiceId, segIds] of grouped) {
        const result = await api.generateTts(projectId, segIds, voiceId || undefined);
        if (result?.segments) merged.push(...result.segments);
      }
      if (merged.length > 0) loadAudio(mergeAudioSegments(audio, merged));
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo TTS").title, "danger");
    } finally {
      setGenerating(false);
      setSelectedIds(new Set());
    }
  }

  async function generateAll() {
    if (!projectId) return;
    setGenerating(true);
    try {
      const ids = translation.map((t) => t.id);
      const result = await api.generateTts(projectId, ids);
      if (result?.segments) {
        loadAudio(mergeAudioSegments(audio, result.segments));
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo TTS").title, "danger");
    } finally {
      setGenerating(false);
    }
  }

  async function generateSegment(segmentId: string) {
    if (!projectId) return;
    setGeneratingIds((prev) => new Set(prev).add(segmentId));
    try {
      const voiceId = getVoiceForSegment(translation.find((t) => t.id === segmentId)!);
      const result = await api.generateTts(projectId, [segmentId], voiceId);
      if (result?.segments) {
        loadAudio(mergeAudioSegments(audio, result.segments));
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo TTS").title, "danger");
    } finally {
      setGeneratingIds((prev) => {
        const next = new Set(prev);
        next.delete(segmentId);
        return next;
      });
    }
  }

  async function previewSegment(segmentId: string) {
    if (!projectId) return;
    const segment = translation.find((t) => t.id === segmentId);
    if (!segment) return;
    setPreviewingId(segmentId);
    try {
      const voiceId = getVoiceForSegment(segment);
      const result = await api.previewTts(projectId, segment.text || segment.display_text || "", voiceId);
      if (result?.audio_url) {
        window.open(result.audio_url, "_blank");
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể preview TTS").title, "danger");
    } finally {
      setPreviewingId(null);
    }
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
        <input
          type="checkbox"
          checked={selectedIds.size === translation.length}
          onChange={(e) => {
            if (e.target.checked) setSelectedIds(new Set(translation.map((t) => t.id)));
            else setSelectedIds(new Set());
          }}
          style={{ accentColor: theme.accent }}
        />
        <strong style={{ fontSize: 13 }}>TTS Generation</strong>
        <span style={{ fontSize: 11, color: theme.textMuted }}>{translation.length} segments</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <Button
            size="sm"
            disabled={selectedIds.size === 0 || generating}
            onClick={generateForSelected}
          >
            {generating ? "..." : null}
            Tạo đã chọn ({selectedIds.size})
          </Button>
          <Button size="sm" variant="primary" disabled={generating} onClick={generateAll}>
            {generating ? "..." : null}
            Tạo tất cả
          </Button>
        </div>
      </div>
      {translation.map((t) => {
        const speaker = speakers.find((s) => s.id === t.speaker_id);
        const voiceId = getVoiceForSegment(t);
        const voice = voices.find((v) => v.id === voiceId);
        const audioSegment = getAudioForSegment(t.id);
        const isSelected = selectedIds.has(t.id);
        const isGenerating = generatingIds.has(t.id);
        const isPreviewing = previewingId === t.id;

        return (
          <div
            key={t.id}
            style={{
              padding: "10px 12px",
              borderBottom: `1px solid ${theme.border}`,
              display: "grid",
              gridTemplateColumns: "24px 70px 1fr 160px 120px 100px",
              gap: 10,
              alignItems: "center",
              fontSize: 12,
              background: isSelected ? "rgba(125,211,252,0.04)" : "transparent",
            }}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleSelect(t.id)}
              style={{ accentColor: theme.accent }}
            />
            <span
              style={{ fontVariantNumeric: "tabular-nums", color: theme.textMuted, cursor: "pointer" }}
              onClick={() => setTime(t.start_ms)}
            >
              {fmt(t.start_ms)}
            </span>
            <span
              onClick={() => setTime(t.start_ms)}
              style={{ cursor: "pointer", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
              title={t.text || t.display_text || ""}
            >
              {t.display_text || t.text || "—"}
            </span>
            <Select
              value={voiceId ?? ""}
              onChange={(e) => {
                const newVoiceId = e.target.value;
                if (newVoiceId) {
                  setVoiceAssignments((prev) => ({ ...prev, [t.id]: newVoiceId }));
                }
              }}
            >
              <option value="">— Voice —</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.speaker_id ? `Speaker ${v.speaker_id.slice(0, 6)}` : `Voice ${v.id.slice(0, 8)}`}
                </option>
              ))}
            </Select>
            <span style={{ fontSize: 11, display: "flex", alignItems: "center", gap: 4 }}>
              {audioSegment ? (
                <>
                  <span style={{ color: theme.success }}>●</span>
                  Đã tạo
                </>
              ) : (
                <>
                  <span style={{ color: theme.textMuted }}>○</span>
                  Chưa tạo
                </>
              )}
            </span>
            <div style={{ display: "flex", gap: 4 }}>
              <Button
                size="sm"
                variant="ghost"
                disabled={isPreviewing}
                onClick={() => previewSegment(t.id)}
                title="Nghe thử"
              >
                {isPreviewing ? "..." : "▶"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={isGenerating}
                onClick={() => generateSegment(t.id)}
                title="Tạo lại"
              >
                {isGenerating ? "..." : "↻"}
              </Button>
            </div>
          </div>
        );
      })}
    </Card>
  );
}

function fmt(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
