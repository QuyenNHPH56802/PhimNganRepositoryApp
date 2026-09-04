/** Batch processing API client. */
import { api } from "./api";

export interface BatchItemInput {
  title: string;
  asset_filename: string;
  source_language?: string;
  target_language?: string;
  quality_mode?: string;
  language_profile?: string;
  tts_provider_id?: string;
  translate_provider_id?: string;
  glossary_id?: string;
  notify_url?: string;
}

export interface BatchCreate {
  items: BatchItemInput[];
  max_concurrency?: number;
  auto_start?: boolean;
}

export interface BatchItemResult {
  item_index: number;
  title: string;
  project_id: string | null;
  workflow_id: string | null;
  status: "pending" | "running" | "completed" | "failed";
  error: string | null;
}

export interface BatchStatus {
  batch_id: string;
  created_at: string;
  state: "queued" | "running" | "completed" | "partial_failure" | "failed";
  max_concurrency: number;
  items: BatchItemResult[];
  summary: { total?: number; completed: number; failed: number; pending?: number };
}

export interface BatchCreated {
  batch_id: string;
  accepted: number;
  queued_at: string;
  poll_url: string;
}

export async function createBatch(body: BatchCreate): Promise<BatchCreated> {
  return api.post<BatchCreated>("/batch", body);
}

export async function getBatch(batchId: string): Promise<BatchStatus> {
  return api.get<BatchStatus>(`/batch/${batchId}`);
}

export async function deleteBatch(batchId: string): Promise<void> {
  await api.delete(`/batch/${batchId}`);
}
