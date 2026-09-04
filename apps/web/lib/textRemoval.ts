/** Text removal API client. */
import { api } from "./api";

export interface TextRemovalJob {
  id: string;
  project_id: string;
  source_asset_id: string;
  region_ids: string[];
  provider_id: string;
  strategy: string;
  status: "queued" | "running" | "completed" | "failed";
  output_asset_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TextRemovalJobInput {
  provider_id?: string;
  strategy?: "inpaint_lama" | "inpaint_anything" | "telea";
  region_ids?: string[];
  asset_id?: string;
}

export interface TextRemovalJobCreateOutput {
  job: TextRemovalJob;
  region_count: number;
}

export async function listTextRemovalJobs(projectId: string): Promise<TextRemovalJob[]> {
  return api.get<TextRemovalJob[]>(`/projects/${projectId}/text-removal/jobs`);
}

export async function createTextRemovalJob(
  projectId: string,
  body: TextRemovalJobInput,
): Promise<TextRemovalJobCreateOutput> {
  return api.post<TextRemovalJobCreateOutput>(`/projects/${projectId}/text-removal/jobs`, body);
}

export async function deleteTextRemovalJob(projectId: string, jobId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/text-removal/jobs/${jobId}`);
}
