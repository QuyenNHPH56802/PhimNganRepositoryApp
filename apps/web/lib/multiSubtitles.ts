/** Multi-language subtitle API client. */
import { api } from "./api";

export interface SubtitleLanguage {
  code: string;
  label: string;
  is_default: boolean;
}

export interface SubtitleLine {
  id: string;
  idx: number;
  start_ms: number;
  end_ms: number;
  text: string;
}

export interface LanguageTrack {
  language_code: string;
  language_label: string;
  track_id: string | null;
  segments: SubtitleLine[];
  segment_count: number;
}

export interface GenerateMultiSubtitlesResponse {
  project_id: string;
  languages: LanguageTrack[];
}

export async function listSupportedLanguages(): Promise<SubtitleLanguage[]> {
  return api.get<SubtitleLanguage[]>("/projects/placeholder/subtitles/languages").catch(() => []);
}

export async function listSubtitleTracks(projectId: string): Promise<LanguageTrack[]> {
  return api.get<LanguageTrack[]>(`/projects/${projectId}/subtitles/tracks`);
}

export async function generateMultiSubtitles(
  projectId: string,
  body: { target_languages: string[]; cps_limit?: number },
): Promise<GenerateMultiSubtitlesResponse> {
  return api.post<GenerateMultiSubtitlesResponse>(
    `/projects/${projectId}/subtitles/generate-multi`,
    body,
  );
}
