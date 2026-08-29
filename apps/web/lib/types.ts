export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type QualityMode = "fast" | "balanced" | "high";
export type WorkflowStatus =
  | "draft"
  | "uploading"
  | "uploaded"
  | "analyzing"
  | "asr_processing"
  | "transcript_ready"
  | "translating"
  | "translation_ready"
  | "review"
  | "voice_assignment"
  | "tts_processing"
  | "subtitle_ready"
  | "audio_mixing"
  | "rendering"
  | "completed"
  | "failed"
  | "cancelled"
  | "paused";

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
  text: string;
  confidence?: number;
}

export interface TranslationSegment {
  id: string;
  start_ms: number;
  end_ms: number;
  transcript_segment_id?: string;
  speaker_id?: string | null;
  text: string;
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
  name: string;
  provider_id: string;
  model_id: string;
  voice_id: string;
  default_accent?: string | null;
  consent_status: string;
}

export interface SubtitleSegment {
  id: string;
  track_id: string;
  start_ms: number;
  end_ms: number;
  text: string;
}

export interface AudioSegment {
  id: string;
  track_id: string;
  start_ms: number;
  end_ms: number;
  audio_key: string;
  duration_ms: number;
}

export type Panel =
  | "transcript"
  | "translation"
  | "speaker"
  | "voice"
  | "subtitle"
  | "audio"
  | "render";
