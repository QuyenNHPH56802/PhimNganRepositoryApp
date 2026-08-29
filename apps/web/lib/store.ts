"use client";

import { create } from "zustand";
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

  transcript: TranscriptSegment[];
  translation: TranslationSegment[];
  speakers: Speaker[];
  voices: VoiceProfile[];
  subtitles: SubtitleSegment[];
  audio: AudioSegment[];

  dirty: boolean;
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

  loadTranscript: (rows: TranscriptSegment[]) => void;
  loadTranslation: (rows: TranslationSegment[]) => void;
  loadSpeakers: (rows: Speaker[]) => void;
  loadVoices: (rows: VoiceProfile[]) => void;
  loadSubtitles: (rows: SubtitleSegment[]) => void;
  loadAudio: (rows: AudioSegment[]) => void;

  updateTranslationSegment: (id: string, text: string) => void;
  updateSubtitleSegment: (id: string, patch: Partial<SubtitleSegment>) => void;
  splitSubtitle: (id: string, atMs: number) => void;
  mergeSubtitleWith: (id: string, nextId: string) => void;
  deleteSubtitle: (id: string) => void;
  assignSpeakerToVoice: (speakerId: string, voiceProfileId: string | null) => void;
  renameSpeaker: (id: string, name: string) => void;

  pushHistory: () => void;
  undo: () => void;
  redo: () => void;

  markDirty: () => void;
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

export const useEditor = create<EditorState>((set, get) => ({
  projectId: null,
  panel: "transcript",
  currentTimeMs: 0,
  durationMs: 0,
  playing: false,
  volume: 1,
  zoom: 100,
  selectedSegmentId: null,
  selectedTrackId: null,

  transcript: [],
  translation: [],
  speakers: [],
  voices: [],
  subtitles: [],
  audio: [],

  dirty: false,
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

  loadTranscript: (rows) => set({ transcript: rows }),
  loadTranslation: (rows) => set({ translation: rows }),
  loadSpeakers: (rows) => set({ speakers: rows }),
  loadVoices: (rows) => set({ voices: rows }),
  loadSubtitles: (rows) => set({ subtitles: rows }),
  loadAudio: (rows) => set({ audio: rows }),

  updateTranslationSegment: (id, text) => {
    const before = emptyHistory(get());
    set((s) => ({
      translation: s.translation.map((seg) =>
        seg.id === id ? { ...seg, text, status: "edited" } : seg,
      ),
      dirty: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  updateSubtitleSegment: (id, patch) => {
    const before = emptyHistory(get());
    set((s) => ({
      subtitles: s.subtitles.map((seg) => (seg.id === id ? { ...seg, ...patch } : seg)),
      dirty: true,
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
      const right: SubtitleSegment = {
        ...target,
        id: `${target.id}-${Date.now()}`,
        start_ms: atMs,
      };
      const next = [...s.subtitles];
      next.splice(idx, 1, left, right);
      return { subtitles: next, dirty: true, undoStack: [...s.undoStack.slice(-49), before], redoStack: [] };
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
      return { subtitles: next, dirty: true, undoStack: [...s.undoStack.slice(-49), before], redoStack: [] };
    });
  },
  deleteSubtitle: (id) => {
    const before = emptyHistory(get());
    set((s) => ({
      subtitles: s.subtitles.filter((x) => x.id !== id),
      dirty: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  assignSpeakerToVoice: (speakerId, voiceProfileId) => {
    const before = emptyHistory(get());
    set((s) => ({
      speakers: s.speakers.map((sp) => (sp.id === speakerId ? { ...sp, voice_profile_id: voiceProfileId ?? undefined } : sp)),
      dirty: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },
  renameSpeaker: (id, name) => {
    const before = emptyHistory(get());
    set((s) => ({
      speakers: s.speakers.map((sp) => (sp.id === id ? { ...sp, label: name } : sp)),
      dirty: true,
      undoStack: [...s.undoStack.slice(-49), before],
      redoStack: [],
    }));
  },

  pushHistory: () => {
    const s = get();
    set({ undoStack: [...s.undoStack.slice(-49), emptyHistory(s)], redoStack: [] });
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

  markDirty: () => set({ dirty: true, autosaveStatus: "idle" }),
  markSaved: () => set({ dirty: false, autosaveStatus: "saved", lastSavedAt: Date.now() }),
  setAutosaveStatus: (autosaveStatus) => set({ autosaveStatus }),
}));
