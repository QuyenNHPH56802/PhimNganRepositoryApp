"use client";

import { useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import { useEditor } from "@/lib/store";
import type { Panel } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import { Button, Card, Input } from "@/components/ui";
import { VideoPlayer } from "@/components/VideoPlayer";
import { Timeline } from "@/components/Timeline";
import { TranscriptPanel } from "@/components/panels/TranscriptPanel";
import { TranslationPanel } from "@/components/panels/TranslationPanel";
import { SpeakerPanel } from "@/components/panels/SpeakerPanel";
import { VoicePanel } from "@/components/panels/VoicePanel";
import { TtsPanel } from "@/components/panels/TtsPanel";
import { SubtitlePanel } from "@/components/panels/SubtitlePanel";
import { AudioPanel } from "@/components/panels/AudioPanel";
import { RenderPanel } from "@/components/panels/RenderPanel";
import { theme } from "@/lib/theme";

const tabs: { id: Panel; label: string }[] = [
  { id: "transcript", label: "Transcript" },
  { id: "translation", label: "Translation" },
  { id: "speaker", label: "Speakers" },
  { id: "voice", label: "Voices" },
  { id: "subtitle", label: "Subtitle" },
  { id: "audio", label: "Audio" },
  { id: "render", label: "Render" },
];

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const panel = useEditor((s) => s.panel);
  const setPanel = useEditor((s) => s.setPanel);
  const setProject = useEditor((s) => s.setProject);
  const loadTranscript = useEditor((s) => s.loadTranscript);
  const loadTranslation = useEditor((s) => s.loadTranslation);
  const loadSpeakers = useEditor((s) => s.loadSpeakers);
  const loadVoices = useEditor((s) => s.loadVoices);
  const loadSubtitles = useEditor((s) => s.loadSubtitles);
  const loadAudio = useEditor((s) => s.loadAudio);
  const undo = useEditor((s) => s.undo);
  const redo = useEditor((s) => s.redo);
  const autosaveStatus = useEditor((s) => s.autosaveStatus);

  useEffect(() => {
    setProject(projectId);
  }, [projectId, setProject]);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    (async () => {
      try {
        const [tr, ts, sp, vo, su, au] = await Promise.all([
          api.listTranscript(projectId),
          api.listTranslation(projectId),
          api.listSpeakers(projectId),
          api.listVoices(projectId),
          api.listSubtitles(projectId),
          api.listAudio(projectId),
        ]);
        if (cancelled) return;
        loadTranscript(tr.segments);
        loadTranslation(ts.segments);
        loadSpeakers(sp.items);
        loadVoices(vo.items);
        loadSubtitles(su.segments);
        loadAudio(au.segments);
      } catch {
        // Backend may not have these endpoints yet — fall back to empty state.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId, loadTranscript, loadTranslation, loadSpeakers, loadVoices, loadSubtitles, loadAudio]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      const meta = e.metaKey || e.ctrlKey;
      if (meta && e.key.toLowerCase() === "z" && !e.shiftKey) {
        e.preventDefault();
        undo();
      } else if (meta && (e.key.toLowerCase() === "y" || (e.key.toLowerCase() === "z" && e.shiftKey))) {
        e.preventDefault();
        redo();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo]);

  const PanelEl = useMemo(() => {
    switch (panel) {
      case "transcript": return TranscriptPanel;
      case "translation": return TranslationPanel;
      case "speaker": return SpeakerPanel;
      case "voice": return VoicePanel;
      case "subtitle": return SubtitlePanel;
      case "audio": return AudioPanel;
      case "render": return RenderPanel;
      default: return TranscriptPanel;
    }
  }, [panel]);

  const ActivePanel = PanelEl;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        background: theme.bg,
      }}
    >
      <header
        style={{
          padding: "10px 16px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: theme.bgElevated,
        }}
      >
        <strong style={{ fontSize: 14 }}>Workspace</strong>
        <span style={{ fontSize: 11, color: theme.textMuted }}>project: {projectId.slice(0, 8)}…</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6, alignItems: "center", fontSize: 11, color: theme.textMuted }}>
          <span>
            Autosave: <strong style={{ color: autosaveStatus === "saved" ? theme.success : theme.warn }}>{autosaveStatus}</strong>
          </span>
          <Button size="sm" onClick={undo}>↶ Undo</Button>
          <Button size="sm" onClick={redo}>↷ Redo</Button>
        </div>
      </header>

      <nav
        style={{
          display: "flex",
          gap: 2,
          padding: "8px 16px 0",
          borderBottom: `1px solid ${theme.border}`,
          background: theme.bgElevated,
        }}
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setPanel(t.id)}
            style={{
              padding: "8px 14px",
              borderRadius: "6px 6px 0 0",
              border: `1px solid ${panel === t.id ? theme.border : "transparent"}`,
              borderBottom: panel === t.id ? `1px solid ${theme.bg}` : "1px solid transparent",
              background: panel === t.id ? theme.bg : "transparent",
              color: panel === t.id ? theme.text : theme.textMuted,
              fontSize: 13,
              fontWeight: 600,
              marginBottom: -1,
              cursor: "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) 1fr",
          gap: 12,
          padding: 12,
          overflow: "hidden",
        }}
      >
        <div style={{ minHeight: 0, overflowY: "auto" }}>
          <ActivePanel />
        </div>
        <div style={{ minHeight: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ flex: "0 0 50%", minHeight: 280 }}>
            <VideoPlayer />
          </div>
          <Card title="Project meta" padded>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12 }}>
              <Field label="Title"><Input defaultValue={`Project ${projectId.slice(0, 6)}`} /></Field>
              <Field label="Quality"><Input defaultValue="balanced" disabled /></Field>
              <Field label="Source lang"><Input defaultValue="zh" disabled /></Field>
              <Field label="Target lang"><Input defaultValue="vi" disabled /></Field>
            </div>
          </Card>
        </div>
      </div>

      <Timeline />
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 10, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}
