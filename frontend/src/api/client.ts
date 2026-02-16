const DEFAULT_BASE_URL = "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string, options?: { signal?: AbortSignal }): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      signal: options?.signal,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  buildUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }
}

export const apiClient = new ApiClient();
