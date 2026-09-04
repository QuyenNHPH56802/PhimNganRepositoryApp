/**
 * Glossary client.
 *
 * Calls `/api/projects/{projectId}/glossaries/*` endpoints. A project can have
 * multiple glossary versions but only one is active at a time. Adding a new
 * active glossary deactivates all others.
 */
import { api } from "./api";

export interface GlossaryTerm {
  id: string;
  chinese: string;
  vietnamese: string;
  category?: string | null;
  rule?: string | null;
  priority: number;
  is_active: boolean;
}

export interface Glossary {
  id: string;
  project_id: string;
  name: string;
  version: number;
  created_at: string;
  is_active: boolean;
  terms: GlossaryTerm[];
}

export interface GlossaryTermInput {
  chinese: string;
  vietnamese: string;
  category?: string | null;
  rule?: string | null;
  priority?: number;
}

export interface GlossaryCreate {
  name: string;
  terms: GlossaryTermInput[];
  activate?: boolean;
}

/** Fetch every glossary version for a project (newest first). */
export async function listGlossaries(projectId: string): Promise<Glossary[]> {
  const data = await api.get<Glossary[]>(`/projects/${projectId}/glossaries`);
  return Array.isArray(data) ? data : [];
}

/** Fetch the active glossary, or null if none. */
export async function getActiveGlossary(projectId: string): Promise<Glossary | null> {
  return api.get<Glossary | null>(`/projects/${projectId}/glossaries/active`);
}

/** Create a new glossary version. */
export async function createGlossary(
  projectId: string,
  body: GlossaryCreate,
): Promise<Glossary> {
  return api.post<Glossary>(`/projects/${projectId}/glossaries`, body);
}

/** Mark a glossary version as the active one (deactivates others). */
export async function activateGlossary(
  projectId: string,
  glossaryId: string,
): Promise<void> {
  await api.post(`/projects/${projectId}/glossaries/${glossaryId}/activate`);
}

/** Permanently delete a glossary version. */
export async function deleteGlossary(
  projectId: string,
  glossaryId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/glossaries/${glossaryId}`);
}

/** Append a single term to an existing glossary. */
export async function addTerm(
  projectId: string,
  glossaryId: string,
  body: GlossaryTermInput,
): Promise<Glossary> {
  return api.post<Glossary>(`/projects/${projectId}/glossaries/${glossaryId}/terms`, body);
}

/** Remove a term by id. */
export async function deleteTerm(
  projectId: string,
  glossaryId: string,
  termId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/glossaries/${glossaryId}/terms/${termId}`);
}
