"use client";

import { API_BASE_URL } from "./types";
import { loadToken } from "./auth";

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
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

  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body === undefined ? undefined : opts.body instanceof FormData ? opts.body : JSON.stringify(opts.body),
    signal: opts.signal,
    cache: "no-store",
  });

  if (res.status === 204) return undefined as T;

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = isJson ? payload?.detail ?? payload : payload;
    if (res.status === 401 && typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, detail);
  }
  return payload as T;
}

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

  listProjects: () =>
    request<{ items: Project[]; total: number }>("/projects").then((r) => r.items),
  createProject: (body: {
    title: string;
    source_language: string;
    target_language: string;
    quality_mode: "fast" | "balanced" | "high";
    language_profile: string;
  }) => request<Project>("/projects", { method: "POST", body }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),

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
    request<{ segments: TranscriptSegment[] }>(`/projects/${projectId}/transcript`).catch(
      () => ({ segments: [] as TranscriptSegment[] }),
    ),
  saveTranscript: (projectId: string, segments: TranscriptSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/transcript`, { method: "PUT", body: { segments } }),

  listTranslation: (projectId: string) =>
    request<{ segments: TranslationSegment[] }>(`/projects/${projectId}/translation`).catch(
      () => ({ segments: [] as TranslationSegment[] }),
    ),
  saveTranslation: (projectId: string, segments: TranslationSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/translation`, { method: "PUT", body: { segments } }),

  listSpeakers: (projectId: string) =>
    request<{ items: Speaker[] }>(`/projects/${projectId}/speakers`).catch(() => ({ items: [] as Speaker[] })),
  saveSpeakers: (projectId: string, speakers: Speaker[]) =>
    request<{ ok: true }>(`/projects/${projectId}/speakers`, { method: "PUT", body: { speakers } }),

  listVoices: (projectId: string) =>
    request<{ items: VoiceProfile[] }>(`/projects/${projectId}/voices`).catch(() => ({ items: [] as VoiceProfile[] })),
  saveVoices: (projectId: string, voices: VoiceProfile[]) =>
    request<{ ok: true }>(`/projects/${projectId}/voices`, { method: "PUT", body: { voices } }),

  listAdminVoiceProfiles: (projectId?: string) =>
    request<VoiceProfile[]>(`/admin/voice-profiles${projectId ? `?project_id=${projectId}` : ""}`).catch(
      () => [] as VoiceProfile[],
    ),

  listSubtitles: (projectId: string) =>
    request<{ segments: SubtitleSegment[] }>(`/projects/${projectId}/subtitles`).catch(
      () => ({ segments: [] as SubtitleSegment[] }),
    ),
  saveSubtitles: (projectId: string, segments: SubtitleSegment[]) =>
    request<{ ok: true }>(`/projects/${projectId}/subtitles`, { method: "PUT", body: { segments } }),

  listAudio: (projectId: string) =>
    request<{ segments: AudioSegment[] }>(`/projects/${projectId}/audio`).catch(
      () => ({ segments: [] as AudioSegment[] }),
    ),
};
