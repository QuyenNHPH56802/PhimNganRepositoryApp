/** Project templates API client. */
import { api } from "./api";

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string | null;
  quality_mode: string;
  language_profile: string;
  source_language: string;
  target_language: string;
  tts_provider_id: string | null;
  translate_provider_id: string | null;
  glossary_id: string | null;
  config: Record<string, unknown>;
  created_at: string;
  use_count: number;
}

export type ProjectTemplateInput = Omit<ProjectTemplate, "id" | "created_at" | "use_count">;

export interface TemplateApplyResult {
  template_id: string;
  use_count: number;
  payload: {
    quality_mode: string;
    language_profile: string;
    source_language: string;
    target_language: string;
    tts_provider_id: string | null;
    translate_provider_id: string | null;
    glossary_id: string | null;
    config: Record<string, unknown>;
  };
}

export async function listTemplates(): Promise<ProjectTemplate[]> {
  return api.get<ProjectTemplate[]>("/templates");
}

export async function createTemplate(body: ProjectTemplateInput): Promise<ProjectTemplate> {
  return api.post<ProjectTemplate>("/templates", body);
}

export async function updateTemplate(id: string, body: ProjectTemplateInput): Promise<ProjectTemplate> {
  return api.put<ProjectTemplate>(`/templates/${id}`, body);
}

export async function deleteTemplate(id: string): Promise<void> {
  await api.delete(`/templates/${id}`);
}

export async function duplicateTemplate(id: string): Promise<ProjectTemplate> {
  return api.post<ProjectTemplate>(`/templates/${id}/duplicate`);
}

export async function applyTemplate(id: string): Promise<TemplateApplyResult> {
  return api.post<TemplateApplyResult>(`/templates/${id}/apply`);
}
