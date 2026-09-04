"use client";

import { api } from "./api";

export interface SegmentIssue {
  kind: string;
  message: string;
  severity: "error" | "warn";
}

export interface SegmentScore {
  segment_id: string;
  idx: number;
  source_text: string;
  display_text: string;
  status: string;
  issues: SegmentIssue[];
  passed: boolean;
  qa_status: "pass" | "warn" | "fail";
}

export interface QaStats {
  ratio_min: number | null;
  ratio_max: number | null;
  pinyin_leak_count: number;
  untranslated_count: number;
  glossary_misses: number;
}

export interface QualityReport {
  project_id: string;
  total_segments: number;
  passed_segments: number;
  failed_segments: number;
  warning_segments: number;
  overall_passed: boolean;
  stats: QaStats | null;
  segments: SegmentScore[];
}

export async function getQualityReport(projectId: string): Promise<QualityReport> {
  return api.get<QualityReport>(`/projects/${projectId}/quality`);
}
