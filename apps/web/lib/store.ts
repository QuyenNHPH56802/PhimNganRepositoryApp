"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  TranscriptSegment,
  TranslationSegment,
  Speaker,
  VoiceProfile,
  SubtitleSegment,
  AudioSegment,
  Panel,
} from "./types";

export type { Panel };

interface HistorySnapshot {
  translation: TranslationSegment[];
  transcript: TranscriptSegment[];
  speakers: Speaker[];
  voices: VoiceProfile[];
  subtitles: SubtitleSegment[];
}

interface EditorState {
  projectId: string | null;
  panel: Panel;
  currentTimeMs: number;
  durationMs: number;
  playing: boolean;
  volume: number;
  zoom: number;
  selectedSegmentId: string | null;
  selectedTrackId: string | null;
  renderedVideoSrc: string | null;

  transcript: TranscriptSegment[];
  translation: TranslationSegment[];
  speakers: Speaker[];
  voices: VoiceProfile[];
  subtitles: SubtitleSegment[];
  audio: AudioSegment[];

  // Audio mixing gains for real-time preview
  audioMixGains: Record<string, number>;

  // Per-type dirty flags so each panel can autosave independently without a
  // round-trip when only one of them changed.
  dirty: boolean;
  dirtyTranslation: boolean;
  dirtyTranscript: boolean;
  dirtySubtitles: boolean;
  dirtySpeakers: boolean;
  dirtyVoices: boolean;
  dirtyAudio: boolean;
  autosaveStatus: "idle" | "saving" | "saved" | "error";
  lastSavedAt: number | null;

  undoStack: HistorySnapshot[];
  redoStack: HistorySnapshot[];

  setProject: (id: string) => void;
  setPanel: (panel: Panel) => void;
  setTime: (ms: number) => void;
  setDuration: (ms: number) => void;
  setPlaying: (playing: boolean) => void;
  setVolume: (v: number) => void;
  setZoom: (z: number) => void;
  selectSegment: (id: string | null) => void;
  setRenderedVideoSrc: (src: string | null) => void;
  setAudioMixGain: (trackId: string, gain: number) => void;
  setAudioMixGains: (gains: Record<string, number>) => void;

  loadTranscript: (rows: TranscriptSegment[]) => void;
  loadTranslation: (rows: TranslationSegment[]) => void;
  loadSpeakers: (rows: Speaker[]) => void;
  loadVoices: (rows: VoiceProfile[]) => void;
  loadSubtitles: (rows: SubtitleSegment[]) => void;
  loadAudio: (rows: AudioSegment[]) => void;

  updateTranslationSegment: (id: string, text?: string, status?: TranslationSegment["status"]) => void;
  updateSubtitleSegment: (id: string, patch: Partial<SubtitleSegment>) => void;
  splitSubtitle: (id: string, atMs: number) => void;
  mergeSubtitleWith: (id: string, nextId: string) => void;
  deleteSubtitle: (id: string) => void;
  assignSpeakerToVoice: (speakerId: string, voiceProfileId: string | null) => void;
  renameSpeaker: (id: string, name: string) => void;

  pushHistory: () => void;
  undo: () => void;
  redo: () => void;

  markDirty: (kind?: "translation" | "subtitles" | "speakers" | "voices" | "audio") => void;
  markSaved: () => void;
  setAutosaveStatus: (s: EditorState["autosaveStatus"]) => void;
}

const emptyHistory = (s: EditorState): HistorySnapshot => ({
  translation: s.translation,
  transcript: s.transcript,
  speakers: s.speakers,
  voices: s.voices,
  subtitles: s.subtitles,
});

export const useEditor = create<EditorState>()(
  persist(
    (set, get) => ({
  projectId: null,
  panel: "transcript",
  currentTimeMs: 0,
  durationMs: 0,
  playing: false,
  volume: 1,
  zoom: 100,
  selectedSegmentId: null,
  selectedTrackId: null,
  renderedVideoSrc: null,

  transcript: [],
  translation: [],
  speakers: [],
  voices: [],
  subtitles: [],
  audio: [],

  audioMixGains: { original: 1, voice_vi: 1, music: 0.5, sfx: 0.7 },

  dirty: false,
  dirtyTranslation: false,
  dirtyTranscript: false,
  dirtySubtitles: false,
  dirtySpeakers: false,
  dirtyVoices: false,
  dirtyAudio: false,
  autosaveStatus: "idle",
  lastSavedAt: null,

  undoStack: [],
  redoStack: [],

  setProject: (id) => set({ projectId: id }),
  setPanel: (panel) => set({ panel }),
  setTime: (ms) => set({ currentTimeMs: ms }),
  setDuration: (ms) => set({ durationMs: ms }),
  setPlaying: (playing) => set({ playing }),
  setVolume: (v) => set({ volume: Math.max(0, Math.min(1, v)) }),
  setZoom: (z) => set({ zoom: Math.max(10, Math.min(1000, z)) }),
  selectSegment: (id) => set({ selectedSegmentId: id }),
  setRenderedVideoSrc: (renderedVideoSrc) => set({ renderedVideoSrc }),
  setAudioMixGain: (trackId, gain) =>
    set((s) => ({
      audioMixGains: { ...s.audioMixGains, [trackId]: gain },
    })),
  setAudioMixGains: (gains) => set({ audioMixGains: gains }),

  loadTranscript: (rows) => set({ transcript: rows }),
  loadTranslation: (rows) => set({ translation: rows, dirtyTranslation: false }),
  loadSpeakers: (rows) => set({ speakers: rows, dirtySpeakers: false }),
  loadVoices: (rows) => set({ voices: rows, dirtyVoices: false }),
  loadSubtitles: (rows) => set({ subtitles: rows, dirtySubtitles: false }),
  loadAudio: (rows) => set({ audio: rows, dirtyAudio: false }),

  updateTranslationSegment: (id, text, status) => {
    const before = emptyHistory(get());
    set((s) => ({
      translation: s.translation.map((seg) =>
        seg.id === id
          ? {
              ...seg,
              ...(text !== undefined && { text, display_text: text }),
              // Preserve existing tts_text unless caller explicitly updates it.
              ...(seg.tts_text === undefined || seg.tts_text === null || seg.tts_text === ""
                ? { tts_text: text ?? seg.tts_text }
                : {}),
              status: status ?? "edited",
            }
          : seg,
      ),
      dirty: true,
      dirtyTranslation: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  updateSubtitleSegment: (id, patch) => {
    const before = emptyHistory(get());
    set((s) => ({
      subtitles: s.subtitles.map((seg) => (seg.id === id ? { ...seg, ...patch } : seg)),
      dirty: true,
      dirtySubtitles: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  splitSubtitle: (id, atMs) => {
    const before = emptyHistory(get());
    set((s) => {
      const idx = s.subtitles.findIndex((x) => x.id === id);
      if (idx === -1) return {};
      const target = s.subtitles[idx];
      if (!target) return {};
      if (atMs <= target.start_ms || atMs >= target.end_ms) return {};
      const left: SubtitleSegment = { ...target, end_ms: atMs };
      const newId =
        typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `${target.id}-${Date.now()}`;
      const right: SubtitleSegment = {
        ...target,
        id: newId,
        start_ms: atMs,
      };
      const next = [...s.subtitles];
      next.splice(idx, 1, left, right);
      return {
        subtitles: next,
        dirty: true,
        dirtySubtitles: true,
        undoStack: [...s.undoStack.slice(-49), before],
        redoStack: [],
      };
    });
  },
  mergeSubtitleWith: (id, nextId) => {
    const before = emptyHistory(get());
    set((s) => {
      const a = s.subtitles.find((x) => x.id === id);
      const b = s.subtitles.find((x) => x.id === nextId);
      if (!a || !b) return {};
      const merged: SubtitleSegment = { ...a, end_ms: b.end_ms, text: `${a.text} ${b.text}`.trim() };
      const next = s.subtitles.filter((x) => x.id !== nextId).map((x) => (x.id === id ? merged : x));
      return {
        subtitles: next,
        dirty: true,
        dirtySubtitles: true,
        undoStack: [...s.undoStack.slice(-49), before],
        redoStack: [],
      };
    });
  },
  deleteSubtitle: (id) => {
    const before = emptyHistory(get());
    set((s) => ({
      subtitles: s.subtitles.filter((x) => x.id !== id),
      dirty: true,
      dirtySubtitles: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  assignSpeakerToVoice: (speakerId, voiceProfileId) => {
    const before = emptyHistory(get());
    set((s) => ({
      speakers: s.speakers.map((sp) => (sp.id === speakerId ? { ...sp, voice_profile_id: voiceProfileId ?? undefined } : sp)),
      dirty: true,
      dirtySpeakers: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  renameSpeaker: (id, name) => {
    const before = emptyHistory(get());
    set((s) => ({
      speakers: s.speakers.map((sp) => (sp.id === id ? { ...sp, label: name } : sp)),
      dirty: true,
      dirtySpeakers: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },

  pushHistory: () => {
    const s = get();
    set({ undoStack: [...s.undoStack.slice(-49), emptyHistory(s)], redoStack: [] });
  },

  markDirty: (kind) => {
    if (!kind) {
      set({ dirty: true, autosaveStatus: "idle" });
      return;
    }
    const flagKey = `dirty${kind[0]!.toUpperCase()}${kind.slice(1)}` as
      | "dirtyTranslation"
      | "dirtySubtitles"
      | "dirtySpeakers"
      | "dirtyVoices"
      | "dirtyAudio";
    set((s) => ({ ...s, [flagKey]: true, dirty: true, autosaveStatus: "idle" }));
  },

  undo: () => {
    const s = get();
    if (s.undoStack.length === 0) return;
    const previous = s.undoStack[s.undoStack.length - 1];
    if (!previous) return;
    const current = emptyHistory(s);
    set({
      transcript: previous.transcript,
      translation: previous.translation,
      speakers: previous.speakers,
      voices: previous.voices,
      subtitles: previous.subtitles,
      undoStack: s.undoStack.slice(0, -1),
      redoStack: [...s.redoStack, current],
    });
  },
  redo: () => {
    const s = get();
    if (s.redoStack.length === 0) return;
    const next = s.redoStack[s.redoStack.length - 1];
    if (!next) return;
    const current = emptyHistory(s);
    set({
      transcript: next.transcript,
      translation: next.translation,
      speakers: next.speakers,
      voices: next.voices,
      subtitles: next.subtitles,
      redoStack: s.redoStack.slice(0, -1),
      undoStack: [...s.undoStack, current],
    });
  },

  markSaved: () =>
    set({
      dirty: false,
      dirtyTranslation: false,
      dirtyTranscript: false,
      dirtySubtitles: false,
      dirtySpeakers: false,
      dirtyVoices: false,
      dirtyAudio: false,
      autosaveStatus: "saved",
      lastSavedAt: Date.now(),
    }),
  setAutosaveStatus: (autosaveStatus) => set({ autosaveStatus }),
}),
{
    name: "translator-editor-state",
    // Only persist navigation/playback state — domain arrays and undo
    // history live in the backend / memory so we don't blow up storage.
    partialize: (s) => ({
      currentTimeMs: s.currentTimeMs,
      selectedSegmentId: s.selectedSegmentId,
      zoom: s.zoom,
      volume: s.volume,
      panel: s.panel,
      projectId: s.projectId,
    }),
    storage: createJSONStorage(() =>
      typeof window === "undefined"
        ? {
            // SSR fallback — no-op storage so server renders match client.
            getItem: () => null,
            setItem: () => undefined,
            removeItem: () => undefined,
          }
        : window.localStorage,
    ),
  },
),
);
