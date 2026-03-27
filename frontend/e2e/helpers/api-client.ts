/**
 * Helper to interact directly with the Backend API during tests
 * Used for setup, cleanup and state verification.
 * 
 * Uses standard fetch to avoid any Playwright request context issues.
 */
export class ApiClient {
  private baseURL = process.env.E2E_API_BASE_URL || 'http://localhost:8000';
  public token: string | null = null;

  constructor(token?: string) {
    if (token) this.token = token;
  }

  setToken(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Authorization': this.token ? `Bearer ${this.token}` : '',
      'Content-Type': 'application/json',
    };
  }

  async get(endpoint: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return {
      status: () => response.status,
      ok: () => response.ok,
      json: async () => await response.json(),
      text: async () => await response.text(),
    };
  }

  async post(endpoint: string, data: any) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return {
      status: () => response.status,
      ok: () => response.ok,
      json: async () => await response.json(),
      text: async () => await response.text(),
    };
  }

  async put(endpoint: string, data: any) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return {
      status: () => response.status,
      ok: () => response.ok,
      json: async () => await response.json(),
      text: async () => await response.text(),
    };
  }

  async delete(endpoint: string) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return {
      status: () => response.status,
      ok: () => response.ok,
      json: async () => await response.json(),
      text: async () => await response.text(),
    };
  }
}
