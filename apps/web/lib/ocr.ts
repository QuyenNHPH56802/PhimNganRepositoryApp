/** OCR API client. */
import { api } from "./api";

export interface OcrBbox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface OcrRegion {
  id: string;
  frame_index: number;
  frame_ts_ms: number;
  bbox: OcrBbox;
  source_text: string;
  translated_text: string | null;
  confidence: number | null;
  status: "pending" | "translated" | "approved" | "rejected";
  provider_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface OcrRegionList {
  regions: OcrRegion[];
  total: number;
  by_status: Record<string, number>;
}

export interface OcrRunInput {
  frame_count?: number;
  start_ts_ms?: number;
  language_hint?: string;
  provider_id?: string;
}

export interface OcrRunResult {
  project_id: string;
  frame_count: number;
  regions_created: number;
  total_regions: number;
}

export async function runOcr(projectId: string, body: OcrRunInput): Promise<OcrRunResult> {
  return api.post<OcrRunResult>(`/projects/${projectId}/ocr/run`, body);
}

export async function listOcrRegions(
  projectId: string,
  statusFilter?: string,
  limit = 100,
): Promise<OcrRegionList> {
  const params = new URLSearchParams();
  if (statusFilter) params.set("status", statusFilter);
  params.set("limit", String(limit));
  return api.get<OcrRegionList>(`/projects/${projectId}/ocr/regions?${params.toString()}`);
}

export async function patchOcrRegion(
  projectId: string,
  regionId: string,
  body: { translated_text?: string | null; status?: string },
): Promise<OcrRegion> {
  return api.patch<OcrRegion>(`/projects/${projectId}/ocr/regions/${regionId}`, body);
}

export async function approveOcrRegion(projectId: string, regionId: string): Promise<OcrRegion> {
  return api.post<OcrRegion>(`/projects/${projectId}/ocr/regions/${regionId}:approve`);
}

export async function deleteOcrRegion(projectId: string, regionId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/ocr/regions/${regionId}`);
}
