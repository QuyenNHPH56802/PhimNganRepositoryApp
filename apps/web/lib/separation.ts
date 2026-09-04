/** Audio separation API client. */
import { api } from "./api";

export interface SeparationTrack {
  id: string;
  kind: string;
  storage_key: string;
  download_url: string;
  provider_id: string;
  duration_ms: number;
  sample_rate: number;
  confidence: number | null;
  created_at: string;
}

export interface SeparationRunInput {
  provider_id?: string;
  method?: string;
  segment_size?: number;
}

export interface SeparationRunOutput {
  project_id: string;
  provider_id: string;
  method: string;
  tracks: SeparationTrack[];
}

export async function runSeparation(
  projectId: string,
  body: SeparationRunInput,
): Promise<SeparationRunOutput> {
  return api.post<SeparationRunOutput>(`/projects/${projectId}/separation/run`, body);
}

export async function listSeparationTracks(
  projectId: string,
  kind?: string,
): Promise<SeparationTrack[]> {
  const q = kind ? `?kind=${kind}` : "";
  return api.get<SeparationTrack[]>(`/projects/${projectId}/separation/tracks${q}`);
}

export async function deleteSeparationTrack(
  projectId: string,
  trackId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/separation/tracks/${trackId}`);
}
