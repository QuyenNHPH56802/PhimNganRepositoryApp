"use client";

import { API_BASE_URL } from "./types";
import { loadToken } from "./auth";

/** Convert a relative `/local-assets/...` path returned by the backend into a
 * URL the browser can fetch. When the web container cannot reach the API
 * directly (typical Docker setup), route through the Next.js proxy. */
function toAssetProxyUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  if (value.startsWith("/local-assets/")) {
    return `/api/proxy-video?path=${encodeURIComponent(value)}`;
  }
  // Already absolute (http(s)://...) or a path the browser can resolve.
  return value;
}

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(opts.headers ?? {}),
  };
  const token = loadToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body !== undefined && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // GETs use the browser cache so identical refreshes don't re-hit the API;
  // mutations (POST/PUT/DELETE/PATCH) always bypass cache to avoid stale reads.
  const method = (opts.method ?? "GET").toUpperCase();
  const isMutation = method !== "GET";

  const res = await fetch(url, {
    method,
    headers,
    body: opts.body === undefined ? undefined : opts.body instanceof FormData ? opts.body : JSON.stringify(opts.body),
    signal: opts.signal,
    cache: isMutation ? "no-store" : "default",
  });

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = isJson ? payload?.detail ?? payload : payload;
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, detail);
  }
  return payload as T;
}

// ─── Public helpers (thin wrappers around `request`) ────────────────────
// Useful for one-off endpoints that don't deserve a dedicated method on
// `api`. All wrappers respect the same auth, headers, and error semantics.
export async function get<T>(path: string, opts?: RequestOptions): Promise<T> {
  return request<T>(path, { ...(opts ?? {}), method: "GET" });
}

export async function post<T>(
  path: string,
  body?: unknown,
  opts?: RequestOptions,
): Promise<T> {
  return request<T>(path, { ...(opts ?? {}), method: "POST", body });
}

export async function put<T>(
  path: string,
  body?: unknown,
  opts?: RequestOptions,
): Promise<T> {
  return request<T>(path, { ...(opts ?? {}), method: "PUT", body });
}

export async function patch<T>(
  path: string,
  body?: unknown,
  opts?: RequestOptions,
): Promise<T> {
  return request<T>(path, { ...(opts ?? {}), method: "PATCH", body });
}

export async function del<T = void>(path: string, opts?: RequestOptions): Promise<T> {
  return request<T>(path, { ...(opts ?? {}), method: "DELETE" });
}

// Convenience exports — `api.delete` is a reserved word in some JS engines,
// so callers can use the named helpers above instead.
export const deleteRequest = del;

import type {
  Project,
  Workflow,
  WorkflowStep,
  ProviderConfig,
  Capabilities,
  AssetPresignResponse,
  TranscriptSegment,
  TranslationSegment,
  Speaker,
  VoiceProfile,
  SubtitleSegment,
  AudioSegment,
} from "./types";

export const api = {
  capabilities: () => request<Capabilities>("/capabilities"),

  getAssetUrl: (projectId: string) =>
    request<{ url: string | null; asset_id: string | null; rendered_url?: string | null }>(`/projects/${projectId}/asset-url`).catch(
      () => ({ url: null, asset_id: null, rendered_url: null }),
    ).then((r) => ({
      ...r,
      // Backend returns relative /local-assets/... paths; convert to a URL the
      // browser can fetch through Next's proxy when web runs in Docker.
      url: toAssetProxyUrl(r.url),
      rendered_url: toAssetProxyUrl(r.rendered_url ?? null),
    })),

  listProjects: () =>
    request<{ items: Project[]; total: number }>("/projects").then((r) => r.items),
  createProject: (body: {
    title: string;
    source_language: string;
    target_language: string;
    quality_mode: "fast" | "balanced" | "high";
    language_profile: string;
    tts_provider_id?: string;
    tts_config?: Record<string, unknown>;
    translate_provider_id?: string;
    translate_config?: Record<string, unknown>;
  }) => request<Project>("/projects", { method: "POST", body }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  deleteProject: (id: string) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  presignAsset: (projectId: string, body: { filename: string; mime: string; size: number }) =>
    request<AssetPresignResponse>(`/projects/${projectId}/assets:presign`, {
      method: "POST",
      body,
    }),

  triggerWorkflow: (projectId: string, body: { quality_mode?: "fast" | "balanced" | "high" }) =>
    request<{ workflow_id: string; run_id: string }>(`/projects/${projectId}/workflows`, {
      method: "POST",
      body,
    }),
  getWorkflow: (projectId: string, workflowId: string) =>
    request<Workflow>(`/projects/${projectId}/workflows/${workflowId}`),
  listWorkflowSteps: (projectId: string, workflowId: string) =>
    request<WorkflowStep[]>(`/projects/${projectId}/workflows/${workflowId}/steps`),

  listProviderConfigs: (projectId: string, kind?: string) =>
    request<ProviderConfig[]>(
      `/projects/${projectId}/provider-configs${kind ? `?kind=${kind}` : ""}`,
    ),
  upsertProviderConfig: (
    projectId: string,
    body: {
      provider_kind: string;
      provider_id: string;
      config?: Record<string, unknown>;
      is_active: boolean;
    },
  ) => request<ProviderConfig>(`/projects/${projectId}/provider-configs`, { method: "PUT", body }),

  listTranscript: (projectId: string) =>
    request<{ segments: TranscriptSegment[] }>(`/projects/${projectId}/transcript`),
  saveTranscript: (projectId: string, segments: TranscriptSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/transcript`, { method: "PUT", body: { segments } }),

  listTranslation: (projectId: string) =>
    request<{ segments: TranslationSegment[] }>(`/projects/${projectId}/translation`),
  saveTranslation: (projectId: string, segments: TranslationSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/translation`, { method: "PUT", body: { segments } }),

  listSpeakers: (projectId: string) =>
    request<{ items: Speaker[] }>(`/projects/${projectId}/speakers`),
  saveSpeakers: (projectId: string, speakers: Speaker[]) =>
    request<{ ok: true }>(`/projects/${projectId}/speakers`, { method: "PUT", body: { speakers } }),

  listVoices: (projectId: string) =>
    request<{ items: VoiceProfile[] }>(`/projects/${projectId}/voices`),
  saveVoices: (projectId: string, voices: VoiceProfile[]) =>
    request<{ ok: true }>(`/projects/${projectId}/voices`, { method: "PUT", body: { voices } }),

  // Admin endpoints always go through the Next.js proxy so the backend can
  // stay internal and the request can carry the user's session cookie or
  // bearer token in one place.
  listAdminVoiceProfiles: (projectId?: string) =>
    request<VoiceProfile[]>(`/api/admin/voice-profiles${projectId ? `?project_id=${projectId}` : ""}`),

  listSubtitles: (projectId: string) =>
    request<{ segments: SubtitleSegment[] }>(`/projects/${projectId}/subtitles`),
  saveSubtitles: (projectId: string, segments: SubtitleSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/subtitles`, { method: "PUT", body: { segments } }),

  listAudio: (projectId: string) =>
    request<{ segments: AudioSegment[] }>(`/projects/${projectId}/audio`),
  // Audio segments are derived from TTS jobs; they don't have a user-editable
  // PUT endpoint. Keep this stub so callers can wire autosave symmetrically.
  saveAudio: (_projectId: string, _segments: AudioSegment[]) =>
    Promise.resolve({ ok: true as const }),

  // Translation
  regenerateTranslation: (projectId: string, segmentId: string) =>
    request<{ id: string; display_text: string; tts_text: string }>(
      `/projects/${projectId}/translation/${segmentId}/regenerate`,
      { method: "POST" }
    ).catch(() => null),

  // TTS
  generateTts: (projectId: string, segmentIds: string[], voiceId?: string) =>
    request<{ ok: boolean; segments: AudioSegment[] }>(`/projects/${projectId}/tts/generate`, {
      method: "POST",
      body: { segment_ids: segmentIds, voice_id: voiceId },
    }),

  previewTts: (projectId: string, text: string, voiceId?: string) =>
    request<{ audio_url: string | null; error?: string }>(`/projects/${projectId}/tts/preview`, {
      method: "POST",
      body: { text, voice_id: voiceId },
    }),

  // Render video
  renderVideo: (projectId: string, config: {
    resolution?: string;
    codec?: string;
    audio_mode?: string;
    burn_subtitle?: boolean;
    quality_mode?: string;
  }) =>
    request<{ ok: boolean; rendered_url?: string | null; storage_key?: string; error?: string }>(
      `/projects/${projectId}/render`,
      { method: "POST", body: config }
    ),

  // Subtitle
  generateSubtitles: (projectId: string) =>
    request<{ ok: true; segments: SubtitleSegment[] }>(`/projects/${projectId}/subtitles/generate`, {
      method: "POST",
    }),

  // Audio
  autoMixAudio: (projectId: string, gains: Record<string, number>) =>
    request<{ ok: true; gains: Record<string, number> }>(`/projects/${projectId}/audio/auto-mix`, {
      method: "POST",
      body: { gains },
    }),

  renderAudioMix: (projectId: string, gains: Record<string, number>) =>
    request<{ ok: true; audio_url: string }>(`/projects/${projectId}/audio/render`, {
      method: "POST",
      body: { gains },
    }),

  // Music upload
  presignMusicAsset: (projectId: string, body: { filename: string; mime: string; size: number }) =>
    request<{ asset_id: string; key: string; url: string; headers: Record<string, string>; expires_in: number }>(
      `/projects/${projectId}/music:presign`,
      { method: "POST", body }
    ),

  createMusicTrack: (projectId: string, body: { asset_id: string }) =>
    request<{ ok: true; track_id: string; storage_key: string }>(`/projects/${projectId}/music`, {
      method: "POST",
      body,
    }),

  getMusicTrack: (projectId: string) =>
    request<{ music: any }>(`/projects/${projectId}/music`),

  // Voice
  createVoiceProfile: (projectId: string, body: Partial<VoiceProfile>) =>
    request<VoiceProfile>(`/projects/${projectId}/voices`, { method: "POST", body }),
  previewVoice: (projectId: string, voiceId: string, text?: string) =>
    request<{ audio_url: string }>(`/projects/${projectId}/voices/${voiceId}/preview`, {
      method: "POST",
      body: { text: text ?? "Xin chào, đây là giọng nói mẫu." },
    }),
};
