export type QualityMode = "fast" | "balanced" | "high";

// Single source of truth for the backend base URL.
// - In Docker, the web container reaches the API container at `api:8000`.
// - In dev, the browser reaches the local backend at `localhost:8000`.
// `next.config.mjs` forwards NEXT_PUBLIC_API_BASE_URL to the client bundle;
// the DOCKER_CONTAINER check lets the same bundle work inside Docker.
function resolveApiBaseUrl(): string {
  if (process.env.DOCKER_CONTAINER === "true") {
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://api:8000";
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export const API_BASE_URL = resolveApiBaseUrl();

export type WorkflowStatus =
  | "draft"
  | "processing"
  | "awaiting_review"
  | "ready"
  | "archived"
  | "failed";

export interface Project {
  id: string;
  title: string;
  quality_mode: QualityMode;
  status: WorkflowStatus;
  created_at: string;
}

export interface Workflow {
  id: string;
  workflow_id: string;
  run_id: string;
  status: WorkflowStatus;
  quality_mode: QualityMode;
  last_error?: string | null;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: string;
  attempt: number;
  progress_pct: number;
  progress_message?: string | null;
}

export interface ProviderConfig {
  id: string;
  provider_kind: string;
  provider_id: string;
  config?: Record<string, unknown>;
  is_active: boolean;
}

export interface Capabilities {
  features: Record<string, boolean>;
  providers: Record<string, Array<{ provider_id: string; is_stub: boolean }>>;
}

export interface AssetPresignResponse {
  key: string;
  url: string;
  headers: Record<string, string>;
  expires_in: number;
}

export interface TranscriptSegment {
  id: string;
  start_ms: number;
  end_ms: number;
  speaker_id?: string | null;
  text?: string;
  raw_text?: string;
  normalized_text?: string;
  confidence?: number;
}

export interface TranslationSegment {
  id: string;
  start_ms: number;
  end_ms: number;
  transcript_segment_id?: string;
  speaker_id?: string | null;
  text?: string;
  display_text?: string;
  tts_text?: string;
  status: "auto" | "review" | "edited" | "approved" | "error";
}

export interface Speaker {
  id: string;
  label: string;
  gender?: "male" | "female" | "unknown";
  voice_profile_id?: string | null;
}

export interface VoiceProfile {
  id: string;
  project_id: string;
  speaker_id?: string | null;
  consent_status: string;
  reference_audio_key?: string | null;
}

export interface SubtitleSegment {
  id: string;
  track_id?: string;
  start_ms: number;
  end_ms: number;
  text?: string;
  display_text?: string;
}

export interface AudioSegment {
  id: string;
  track_id?: string;
  start_ms: number;
  end_ms: number;
  audio_key?: string;
  storage_key?: string;
  duration_ms?: number;
  translation_segment_id?: string;
  source?: string;
}

export type Panel =
  | "transcript"
  | "translation"
  | "speaker"
  | "voice"
  | "subtitle"
  | "audio"
  | "render";
