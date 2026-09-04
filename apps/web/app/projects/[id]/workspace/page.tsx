"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useEditor } from "@/lib/store";
import type { Panel } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import { API_BASE_URL } from "@/lib/types";
import { Button, Card, EmptyState, Input, ProgressBar, StatusDot } from "@/components/ui";
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
import { ProgressPanel } from "@/components/panels/ProgressPanel";
import { GlossaryEditor } from "@/components/GlossaryEditor";
import { useWorkflowStream } from "@/lib/useWorkflowStream";
import { useShortcuts } from "@/lib/useShortcuts";
import { ShortcutsHelp } from "@/components/ShortcutsHelp";
import { useToast } from "@/lib/toast";
import { theme } from "@/lib/theme";

const tabs: { id: Panel; label: string }[] = [
  { id: "transcript", label: "Bản ghi" },
  { id: "translation", label: "Bản dịch" },
  { id: "speaker", label: "Người nói" },
  { id: "voice", label: "Giọng nói" },
  { id: "subtitle", label: "Phụ đề" },
  { id: "audio", label: "Âm thanh" },
  { id: "render", label: "Render" },
  { id: "glossary", label: "Glossary" },
  { id: "progress", label: "Tiến trình" },
];

const WORKFLOW_STEP_LABELS: Record<string, string> = {
  ingest: "Tải & chuẩn hoá video",
  asr: "Nhận dạng giọng nói (ASR)",
  align: "Canh chỉnh thời gian",
  diarize: "Phân tách người nói",
  translate: "Dịch Trung → Việt",
  tts: "Tổng hợp giọng nói (TTS)",
  align_audio: "Canh chỉnh audio",
  render: "Render video cuối",
};

const STAGE_WEIGHT: Record<string, number> = {
  ingest: 10,
  asr: 20,
  align: 10,
  diarize: 10,
  translate: 15,
  tts: 20,
  align_audio: 5,
  render: 10,
};

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const panel = useEditor((s) => s.panel);
  const setPanel = useEditor((s) => s.setPanel);
  const setProject = useEditor((s) => s.setProject);
  const setIsInitialLoading = useEditor((s) => s.setIsInitialLoading);
  const isInitialLoading = useEditor((s) => s.isInitialLoading);
  const renderedVideoSrc = useEditor((s) => s.renderedVideoSrc);
  const setRenderedVideoSrc = useEditor((s) => s.setRenderedVideoSrc);
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

  const [rawVideoSrc, setRawVideoSrc] = useState<string | undefined>(undefined);
  const [videoMode, setVideoMode] = useState<"raw" | "rendered">("raw");
  const [projectTitle, setProjectTitle] = useState<string>("");
  const [titleSaving, setTitleSaving] = useState(false);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [projectMissing, setProjectMissing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadErrors, setLoadErrors] = useState<string[]>([]);
  const { toast } = useToast();

  // Fetch project metadata once (no poll) so we can show the real title.
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setProjectTitle("");
    setTitleError(null);
    setProjectMissing(false);
    (async () => {
      try {
        const p = await api.getProject(projectId);
        if (cancelled) return;
        setProjectTitle(p.title ?? "");
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          // Project doesn't exist (or UUID malformed) — show a dedicated empty
          // state instead of a generic placeholder title.
          setProjectMissing(true);
          setProjectTitle("");
          return;
        }
        setProjectTitle(`Dự án ${projectId.slice(0, 6)}`);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function saveTitle() {
    if (!projectId) return;
    const trimmed = projectTitle.trim();
    if (!trimmed) {
      setTitleError("Tiêu đề không được để trống");
      return;
    }
    setTitleSaving(true);
    setTitleError(null);
    try {
      await fetch(`/api/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });
      setTitleSaving(false);
    } catch (error) {
      setTitleError("Lỗi khi lưu tiêu đề project");
      setTitleSaving(false);
    }
  }

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    (async () => {
      try {
        const result: any = await api.getAssetUrl(projectId);
        if (cancelled) return;
        setRawVideoSrc(result.url ?? undefined);
        if (result.rendered_url) {
          setRenderedVideoSrc(result.rendered_url);
          setVideoMode("rendered");
        }
      } catch {
        // No video yet — that's fine for new projects.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const loadPanelData = useCallback(async () => {
    if (!projectId) return;
    setRefreshing(true);
    setLoadErrors([]);
    const errors: string[] = [];

    // Helper: call a list endpoint, swallow 404 (treat as empty), surface others.
    const fetchOrEmpty = async <T,>(
      label: string,
      call: () => Promise<T>,
      onEmpty: () => void,
      onSuccess: (data: T) => void,
    ) => {
      try {
        const data = await call();
        onSuccess(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          // 404 on editor endpoints means "no data yet" — empty state.
          onEmpty();
          return;
        }
        errors.push(`${label}: ${err instanceof Error ? err.message : String(err)}`);
      }
    };

    await Promise.all([
      fetchOrEmpty(
        "transcript",
        () => api.listTranscript(projectId),
        () => loadTranscript([]),
        (data) => loadTranscript(data.segments),
      ),
      fetchOrEmpty(
        "translation",
        () => api.listTranslation(projectId),
        () => loadTranslation([]),
        (data) => loadTranslation(data.segments),
      ),
      fetchOrEmpty(
        "speakers",
        () => api.listSpeakers(projectId),
        () => loadSpeakers([]),
        (data) => loadSpeakers(data.items),
      ),
      fetchOrEmpty(
        "voices",
        () => api.listVoices(projectId),
        () => loadVoices([]),
        (data) => loadVoices(data.items),
      ),
      fetchOrEmpty(
        "subtitles",
        () => api.listSubtitles(projectId),
        () => loadSubtitles([]),
        (data) => loadSubtitles(data.segments),
      ),
      fetchOrEmpty(
        "audio",
        () => api.listAudio(projectId),
        () => loadAudio([]),
        (data) => loadAudio(data.segments),
      ),
    ]);

    if (errors.length > 0) {
      setLoadErrors(errors);
      toast(`Một số panel không tải được: ${errors.join("; ")}`, "danger");
    }
    setRefreshing(false);
    setIsInitialLoading(false);
  }, [
    projectId,
    loadTranscript,
    loadTranslation,
    loadSpeakers,
    loadVoices,
    loadSubtitles,
    loadAudio,
    toast,
    setIsInitialLoading,
  ]);

  useEffect(() => {
    loadPanelData();
  }, [loadPanelData]);

  const shortcutBindings = [
    { combo: "Mod+z", description: "Hoàn tác", handler: () => undo() },
    { combo: "Mod+Shift+z", description: "Làm lại", handler: () => redo() },
    { combo: "Mod+y", description: "Làm lại", handler: () => redo() },
  ];
  useShortcuts(shortcutBindings);
  useShortcuts([
    // Video playback shortcuts (allowed everywhere because most panels don't
    // trap space, but Timeline does — global space is suppressed while editing).
    { combo: "j", description: "Tua lùi 5 giây", handler: () => setTime(Math.max(0, currentTimeMs - 5000)) },
    { combo: "l", description: "Tua tới 5 giây", handler: () => setTime(currentTimeMs + 5000) },
    { combo: "k", description: "Phát / Tạm dừng", handler: () => setPlaying(!playing) },
  ]);

  const translation = useEditor((s) => s.translation);
  const subtitles = useEditor((s) => s.subtitles);
  const speakers = useEditor((s) => s.speakers);
  const voices = useEditor((s) => s.voices);
  const audio = useEditor((s) => s.audio);
  const markSaved = useEditor((s) => s.markSaved);
  const setAutosaveStatus = useEditor((s) => s.setAutosaveStatus);

  // Autosave for translation — fires only when translation becomes dirty
  useEffect(() => {
    if (!projectId) return;
    if (!useEditor.getState().dirtyTranslation) return;
    const snapshot = useEditor.getState().translation;
    const timer = setTimeout(async () => {
      // Re-check the flag — user might have undone the change.
      if (!useEditor.getState().dirtyTranslation) return;
      try {
        setAutosaveStatus("saving");
        await api.saveTranslation(projectId, snapshot);
        // Only clear the flag if the translation hasn't been edited again
        // since we started saving.
        if (useEditor.getState().translation === snapshot) {
          useEditor.setState({ dirtyTranslation: false });
          if (
            !useEditor.getState().dirtySubtitles &&
            !useEditor.getState().dirtySpeakers &&
            !useEditor.getState().dirtyVoices &&
            !useEditor.getState().dirtyAudio
          ) {
            markSaved();
          }
        }
      } catch (err) {
        console.error("Autosave translation failed:", err);
        setAutosaveStatus("error");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [projectId, translation, setAutosaveStatus, markSaved]);

  // Autosave for subtitles — fires only when subtitles become dirty
  useEffect(() => {
    if (!projectId) return;
    if (!useEditor.getState().dirtySubtitles) return;
    const snapshot = useEditor.getState().subtitles;
    const timer = setTimeout(async () => {
      if (!useEditor.getState().dirtySubtitles) return;
      try {
        setAutosaveStatus("saving");
        await api.saveSubtitles(projectId, snapshot);
        if (useEditor.getState().subtitles === snapshot) {
          useEditor.setState({ dirtySubtitles: false });
          if (
            !useEditor.getState().dirtyTranslation &&
            !useEditor.getState().dirtySpeakers &&
            !useEditor.getState().dirtyVoices &&
            !useEditor.getState().dirtyAudio
          ) {
            markSaved();
          }
        }
      } catch (err) {
        console.error("Autosave subtitles failed:", err);
        setAutosaveStatus("error");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [projectId, subtitles, setAutosaveStatus, markSaved]);

  // Autosave for speakers — fires only when speakers become dirty
  useEffect(() => {
    if (!projectId) return;
    if (!useEditor.getState().dirtySpeakers) return;
    const snapshot = useEditor.getState().speakers;
    const timer = setTimeout(async () => {
      if (!useEditor.getState().dirtySpeakers) return;
      try {
        setAutosaveStatus("saving");
        await api.saveSpeakers(projectId, snapshot);
        if (useEditor.getState().speakers === snapshot) {
          useEditor.setState({ dirtySpeakers: false });
          if (
            !useEditor.getState().dirtyTranslation &&
            !useEditor.getState().dirtySubtitles &&
            !useEditor.getState().dirtyVoices &&
            !useEditor.getState().dirtyAudio
          ) {
            markSaved();
          }
        }
      } catch (err) {
        console.error("Autosave speakers failed:", err);
        setAutosaveStatus("error");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [projectId, speakers, setAutosaveStatus, markSaved]);

  // Autosave for voices — fires only when voices become dirty
  useEffect(() => {
    if (!projectId) return;
    if (!useEditor.getState().dirtyVoices) return;
    const snapshot = useEditor.getState().voices;
    const timer = setTimeout(async () => {
      if (!useEditor.getState().dirtyVoices) return;
      try {
        setAutosaveStatus("saving");
        await api.saveVoices(projectId, snapshot);
        if (useEditor.getState().voices === snapshot) {
          useEditor.setState({ dirtyVoices: false });
          if (
            !useEditor.getState().dirtyTranslation &&
            !useEditor.getState().dirtySubtitles &&
            !useEditor.getState().dirtySpeakers &&
            !useEditor.getState().dirtyAudio
          ) {
            markSaved();
          }
        }
      } catch (err) {
        console.error("Autosave voices failed:", err);
        setAutosaveStatus("error");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [projectId, voices, setAutosaveStatus, markSaved]);

  // Autosave audio (no-op stub — backend has no PUT /audio, but keep the
  // wiring symmetric so a future backend change doesn't need UI updates).
  useEffect(() => {
    if (!projectId) return;
    if (!useEditor.getState().dirtyAudio) return;
    const snapshot = useEditor.getState().audio;
    const timer = setTimeout(async () => {
      if (!useEditor.getState().dirtyAudio) return;
      try {
        setAutosaveStatus("saving");
        await api.saveAudio(projectId, snapshot);
        if (useEditor.getState().audio === snapshot) {
          useEditor.setState({ dirtyAudio: false });
          if (
            !useEditor.getState().dirtyTranslation &&
            !useEditor.getState().dirtySubtitles &&
            !useEditor.getState().dirtySpeakers &&
            !useEditor.getState().dirtyVoices
          ) {
            markSaved();
          }
        }
      } catch (err) {
        console.error("Autosave audio failed:", err);
        setAutosaveStatus("error");
      }
    }, 1500);
    return () => clearTimeout(timer);
  }, [projectId, audio, setAutosaveStatus, markSaved]);

  // Resolve workflow_id: prefer "project-<uuid>" pattern used by backend trigger endpoint
  const workflowId = projectId ? `project-${projectId}` : "";
  const { steps: workflowSteps, status: streamStatus, retryCount } = useWorkflowStream(workflowId);

  const { overallPct, orderedSteps, pipelineDone } = useMemo(() => {
    if (!workflowSteps.length) {
      return { overallPct: 0, orderedSteps: [] as typeof workflowSteps, pipelineDone: false };
    }
    const ordered = [...workflowSteps].sort((a, b) => {
      const orderA = Object.keys(STAGE_WEIGHT).indexOf(a.name);
      const orderB = Object.keys(STAGE_WEIGHT).indexOf(b.name);
      return (orderA === -1 ? 999 : orderA) - (orderB === -1 ? 999 : orderB);
    });
    let acc = 0;
    let totalWeight = 0;
    for (const s of ordered) {
      const w = STAGE_WEIGHT[s.name] ?? 5;
      totalWeight += w;
      const ready = s.status === "ready";
      const pct = Math.max(0, Math.min(100, s.progress_pct ?? 0));
      acc += ready ? w : (pct / 100) * w;
    }
    const overall = totalWeight > 0 ? Math.round((acc / totalWeight) * 100) : 0;
    const done = ordered.every(
      (s) => s.status === "ready",
    );
    return { overallPct: overall, orderedSteps: ordered, pipelineDone: done };
  }, [workflowSteps]);

  // Auto-refresh panel data when a pipeline stage finishes (e.g. translation ready)
  useEffect(() => {
    if (!projectId || !pipelineDone) return;
    // Single delayed refresh covers the case where the worker just committed
    // its last step row but the DB transaction hasn't been read-replicated yet.
    const timer = setTimeout(() => {
      loadPanelData();
      api.getAssetUrl(projectId).then((r: any) => {
        if (r.rendered_url && r.rendered_url.startsWith("/local-assets/")) {
          setRenderedVideoSrc(r.rendered_url);
          setVideoMode("rendered");
        }
      }).catch(() => undefined);
    }, 1500);
    return () => clearTimeout(timer);
  }, [pipelineDone, projectId, loadPanelData]);

  const ActivePanel = useMemo(() => {
    if (panel === "progress") {
      return () => <ProgressPanel projectId={projectId} workflowId={workflowId} />;
    }
    if (panel === "glossary") {
      return () => <GlossaryEditor projectId={projectId} />;
    }

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
  }, [panel, projectId, workflowId]);
  const currentVideoSrc = videoMode === "rendered" && renderedVideoSrc ? renderedVideoSrc : rawVideoSrc;

  // Snapshot of all panel data — used to detect "pipeline finished but no
  // output" and render a useful hint instead of 6 silent empty panels.
  const transcriptCount = useEditor((s) => s.transcript.length);
  const translationCount = useEditor((s) => s.translation.length);
  const speakersCount = useEditor((s) => s.speakers.length);
  const voicesCount = useEditor((s) => s.voices.length);
  const subtitlesCount = useEditor((s) => s.subtitles.length);
  const audioCount = useEditor((s) => s.audio.length);
  const allPanelsEmpty =
    transcriptCount === 0 &&
    translationCount === 0 &&
    speakersCount === 0 &&
    voicesCount === 0 &&
    subtitlesCount === 0 &&
    audioCount === 0;

  if (projectMissing) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          background: theme.bg,
          color: theme.text,
          fontFamily: theme.fontSans,
        }}
      >
        <header
          style={{
            padding: "10px 16px",
            borderBottom: `1px solid ${theme.border}`,
            background: theme.bgElevated,
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <strong style={{ fontSize: 14 }}>Không gian làm việc</strong>
        </header>
        <div style={{ flex: 1, display: "grid", placeItems: "center", padding: 24 }}>
          <EmptyState
            title="Project không tồn tại"
            description={`Không tìm thấy project với mã "${projectId}". Có thể project đã bị xóa hoặc URL không đúng.`}
            action={
              <Button onClick={() => (window.location.href = "/projects")} variant="primary">
                ← Quay lại danh sách project
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: theme.bg,
        color: theme.text,
        fontFamily: theme.fontSans,
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
        <strong style={{ fontSize: 14 }}>Không gian làm việc</strong>
        <span style={{ fontSize: 11, color: theme.textMuted }}>Dự án: {projectId.slice(0, 8)}…</span>
        {pipelineDone && (
          <span style={{ fontSize: 11, background: "rgba(16, 185, 129, 0.15)", color: "#10b981", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
            ✓ Video đã xử lý hoàn chỉnh
          </span>
        )}
        {!pipelineDone && orderedSteps.length > 0 && (
          <span style={{ fontSize: 11, background: "rgba(251, 191, 36, 0.15)", color: "#f59e0b", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
            ⏳ Đang xử lý ({overallPct}%)
          </span>
        )}
        <div style={{ marginLeft: "auto", display: "flex", gap: 6, alignItems: "center", fontSize: 11, color: theme.textMuted }}>
          <Button
            size="sm"
            variant="ghost"
            onClick={loadPanelData}
            disabled={refreshing}
            title="Tải lại transcript / translation / speakers / voices / subtitles / audio"
          >
            {refreshing ? "⏳ Đang tải..." : "🔄 Làm mới dữ liệu"}
          </Button>
          <span>
            Tự lưu: <strong style={{ color: autosaveStatus === "saved" ? theme.success : theme.warn }}>{autosaveStatus === "saved" ? "Đã lưu" : "Đang lưu..."}</strong>
          </span>
          <Button size="sm" onClick={undo}>↶ Undo</Button>
          <Button size="sm" onClick={redo}>↷ Redo</Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => window.open(`/projects/${projectId}/quality`, "_blank")}
            title="Mở báo cáo chất lượng dịch"
          >
            📋 Quality
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => window.open(`/projects/${projectId}/subtitles-multi`, "_blank")}
            title="Mở bảng phụ đề đa ngôn ngữ"
          >
            🌐 Multi-sub
          </Button>
          <ShortcutsHelp bindings={shortcutBindings} />
        </div>
      </header>

      <nav
        role="tablist"
        aria-label="Panel workspace"
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
            role="tab"
            aria-selected={panel === t.id}
            aria-controls={`panel-${t.id}`}
            id={`tab-${t.id}`}
            tabIndex={panel === t.id ? 0 : -1}
            onClick={() => setPanel(t.id)}
            onKeyDown={(e) => {
              // Arrow keys cycle through tabs (Roving tabindex).
              if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
              e.preventDefault();
              const idx = tabs.findIndex((x) => x.id === panel);
              const delta = e.key === "ArrowRight" ? 1 : -1;
              const next = (idx + delta + tabs.length) % tabs.length;
              const nextTab = tabs[next];
              if (nextTab) {
                setPanel(nextTab.id);
                queueMicrotask(() => {
                  document.getElementById(`tab-${nextTab.id}`)?.focus();
                });
              }
            }}
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
        className="translator-workspace-grid"
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
        <div
          role="tabpanel"
          id={`panel-${panel}`}
          aria-labelledby={`tab-${panel}`}
          tabIndex={0}
          style={{ minHeight: 0, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}
        >
          {loadErrors.length > 0 && (
            <div
              style={{
                background: "#450a0a",
                color: theme.danger,
                padding: "8px 12px",
                borderRadius: 6,
                fontSize: 12,
                border: "1px solid #7f1d1d",
              }}
            >
              ❌ Một số panel không tải được: {loadErrors.join("; ")}
            </div>
          )}
          {pipelineDone && allPanelsEmpty ? (
            <EmptyState
              title="Pipeline hoàn tất nhưng chưa có dữ liệu"
              description="Worker đã báo ready, nhưng 6 panel vẫn rỗng. Thử làm mới dữ liệu, hoặc mở log worker để kiểm tra."
              action={
                <Button variant="primary" onClick={loadPanelData} disabled={refreshing}>
                  {refreshing ? "⏳ Đang tải..." : "🔄 Làm mới dữ liệu"}
                </Button>
              }
            />
          ) : (
            <ActivePanel />
          )}
        </div>
        <div style={{ minHeight: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          {renderedVideoSrc && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <Button
                size="sm"
                variant={videoMode === "rendered" ? "primary" : "ghost"}
                onClick={() => setVideoMode("rendered")}
              >
                ✨ Video Đã Xử Lý / Lồng Tiếng
              </Button>
              <Button
                size="sm"
                variant={videoMode === "raw" ? "primary" : "ghost"}
                onClick={() => setVideoMode("raw")}
              >
                🎬 Video Gốc
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={() => {
                  if (renderedVideoSrc) {
                    window.open(renderedVideoSrc, "_blank");
                  }
                }}
              >
                📥 Tải Video MP4
              </Button>
            </div>
          )}
          <div style={{ flex: "1 1 50%", minHeight: 280, display: "flex", flexDirection: "column" }}>
            <VideoPlayer src={currentVideoSrc} />
          </div>
          <Card title="Thông tin dự án" padded>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12 }}>
              <Field label="Tiêu đề">
                <div style={{ display: "flex", gap: 6 }}>
                  <Input
                    value={projectTitle}
                    onChange={(e) => setProjectTitle(e.target.value)}
                    placeholder="Tiêu đề dự án"
                  />
                  <Button
                    size="sm"
                    onClick={saveTitle}
                    disabled={titleSaving || !projectTitle.trim()}
                    title="Lưu tiêu đề"
                  >
                    💾
                  </Button>
                </div>
                {titleError && (
                  <div style={{ marginTop: 4, fontSize: 11, color: theme.warn }}>{titleError}</div>
                )}
              </Field>
              <Field label="Chế độ chất lượng">
                <Input defaultValue="Cân bằng" disabled />
              </Field>
              <Field label="Ngôn ngữ nguồn">
                <Input defaultValue="Tiếng Trung (ZH)" disabled />
              </Field>
              <Field label="Ngôn ngữ đích">
                <Input defaultValue="Tiếng Việt (VI)" disabled />
              </Field>
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
