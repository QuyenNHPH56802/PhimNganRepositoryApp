/** Webhook API client. */
import { api } from "./api";

export interface WebhookEvent {
  id: string;
  label: string;
}

export interface Webhook {
  id: string;
  project_id: string;
  url: string;
  description: string | null;
  events: string[];
  is_active: boolean;
  created_at: string;
  secret_preview: string;
}

export interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event: string;
  status_code: number | null;
  success: boolean;
  attempt: number;
  last_error: string | null;
  created_at: string;
}

export interface WebhookList {
  webhooks: Webhook[];
  available_events: WebhookEvent[];
}

export interface WebhookCreate {
  url: string;
  description?: string;
  events?: string[];
  secret?: string;
}

export async function listWebhooks(projectId: string): Promise<WebhookList> {
  return api.get<WebhookList>(`/projects/${projectId}/webhooks`);
}

export async function createWebhook(projectId: string, body: WebhookCreate): Promise<Webhook> {
  return api.post<Webhook>(`/projects/${projectId}/webhooks`, body);
}

export async function deleteWebhook(projectId: string, webhookId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/webhooks/${webhookId}`);
}

export async function toggleWebhook(projectId: string, webhookId: string): Promise<Webhook> {
  return api.post<Webhook>(`/projects/${projectId}/webhooks/${webhookId}/toggle`);
}

export async function testWebhook(projectId: string, webhookId: string): Promise<WebhookDelivery> {
  return api.post<WebhookDelivery>(`/projects/${projectId}/webhooks/${webhookId}/test`);
}

export async function listDeliveries(
  projectId: string,
  webhookId: string,
  limit = 20,
): Promise<WebhookDelivery[]> {
  return api.get<WebhookDelivery[]>(
    `/projects/${projectId}/webhooks/${webhookId}/deliveries?limit=${limit}`,
  );
}
