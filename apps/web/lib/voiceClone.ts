/** Voice cloning API client. */
import { api } from "./api";

export interface VoiceCloneSample {
  id: string;
  project_id: string;
  speaker_id: string | null;
  label: string;
  sample_storage_key: string;
  sample_download_url: string;
  provider_id: string;
  embedding_storage_key: string | null;
  embedding_download_url: string | null;
  preview_storage_key: string | null;
  preview_download_url: string | null;
  quality_score: number | null;
  duration_ms: number;
  status: "queued" | "running" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface VoiceCloneSampleInput {
  label: string;
  sample_storage_key: string;
  speaker_id?: string;
  provider_id?: string;
  duration_ms?: number;
  text_preview?: string;
}

export interface VoiceCloneRunOutput {
  sample_id: string;
  provider_id: string;
  quality_score: number | null;
  embedding_storage_key: string | null;
  preview_storage_key: string | null;
  status: string;
}

export async function listVoiceCloneSamples(projectId: string): Promise<VoiceCloneSample[]> {
  return api.get<VoiceCloneSample[]>(`/projects/${projectId}/voice-clone/samples`);
}

export async function createVoiceCloneSample(
  projectId: string,
  body: VoiceCloneSampleInput,
): Promise<VoiceCloneSample> {
  return api.post<VoiceCloneSample>(`/projects/${projectId}/voice-clone/samples`, body);
}

export async function runVoiceClone(
  projectId: string,
  sampleId: string,
): Promise<VoiceCloneRunOutput> {
  return api.post<VoiceCloneRunOutput>(
    `/projects/${projectId}/voice-clone/samples/${sampleId}/run`,
  );
}

export async function deleteVoiceCloneSample(projectId: string, sampleId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/voice-clone/samples/${sampleId}`);
}
