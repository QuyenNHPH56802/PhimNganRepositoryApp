export interface TranslatorClientOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
  cookie?: string;
}

export interface WorkflowTriggerBody {
  asset_id?: string;
  quality_mode?: string;
  source_language?: string;
  target_language?: string;
}

export class TranslatorApiError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(status: number, body: string) {
    super(`Translator API ${status}: ${body}`);
    this.name = "TranslatorApiError";
    this.status = status;
    this.body = body;
  }
}

export class TranslatorClient {
  private readonly baseUrl: string;
  private readonly defaultHeaders: Record<string, string>;
  private readonly cookie: string | null;

  constructor(options: TranslatorClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? "http://localhost:8000";
    this.defaultHeaders = {
      "content-type": "application/json",
      ...options.headers,
    };
    this.cookie = options.cookie ?? null;
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...this.defaultHeaders,
      ...(this.cookie ? { cookie: this.cookie } : {}),
      ...(init.headers as Record<string, string> ?? {}),
    };

    const response = await fetch(this.baseUrl + path, {
      ...init,
      headers,
    });

    if (!response.ok) {
      throw new TranslatorApiError(response.status, await response.text());
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json() as Promise<T>;
  }

  listProjects<T = unknown>(): Promise<T> {
    return this.request<T>("/projects");
  }

  triggerWorkflow<T = unknown>(projectId: string, body: WorkflowTriggerBody): Promise<T> {
    return this.request<T>(`/projects/${projectId}/workflows`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  setQualityMode<T = unknown>(projectId: string, mode: string): Promise<T> {
    return this.request<T>(`/projects/${projectId}/quality-mode`, {
      method: "PUT",
      body: JSON.stringify({ mode }),
    });
  }

  cancelWorkflow<T = unknown>(workflowId: string): Promise<T> {
    return this.request<T>(`/workflows/${workflowId}/cancel`, {
      method: "POST",
    });
  }
}
