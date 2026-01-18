import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom, timeout } from 'rxjs';
import { environment } from '../environment';
import { HevyStatus } from '../models/integration.model';

@Injectable({
  providedIn: 'root'
})
export class HevyService {
  private apiUrl = `${environment.apiUrl}/integrations/hevy`;
  private TIMEOUT_MS = 10000;

  constructor(private http: HttpClient) {}

  async validateKey(apiKey: string): Promise<{ valid: boolean, count?: number }> {
    return firstValueFrom(
      this.http.post<{ valid: boolean, count?: number }>(`${this.apiUrl}/validate`, { api_key: apiKey }).pipe(timeout(this.TIMEOUT_MS))
    );
  }

  async saveConfig(apiKey: string | null | undefined, enabled: boolean): Promise<void> {
    const payload: any = { enabled };
    if (apiKey !== undefined) {
      payload.api_key = apiKey;
    }
    
    await firstValueFrom(
      this.http.post(`${this.apiUrl}/config`, payload).pipe(timeout(this.TIMEOUT_MS))
    );
  }

  async getStatus(): Promise<HevyStatus> {
    const res = await firstValueFrom(this.http.get<any>(`${this.apiUrl}/status`).pipe(timeout(this.TIMEOUT_MS)));
    // Check if response is null (e.g. 404 handled globally?) 
    // Backend throws 404 if profile not found, so this promise will reject.
    return {
        enabled: res.enabled,
        hasKey: res.has_key,
        apiKeyMasked: res.api_key_masked,
        lastSync: res.last_sync
    };
  }
  
  async getCount(): Promise<number> {
      const res = await firstValueFrom(this.http.get<{count: number}>(`${this.apiUrl}/count`).pipe(timeout(this.TIMEOUT_MS)));
      return res.count;
  }

  async importWorkouts(fromDate: string | null, mode: 'skip_duplicates' | 'overwrite'): Promise<any> {
    return firstValueFrom(
      this.http.post(`${this.apiUrl}/import`, { from_date: fromDate, mode }).pipe(timeout(60000)) // Longer for import
    );
  }

  async getWebhookConfig(): Promise<{ has_webhook: boolean, webhook_url?: string, auth_header?: string }> {
    return firstValueFrom(
      this.http.get<{ has_webhook: boolean, webhook_url?: string, auth_header?: string }>(`${this.apiUrl}/webhook/config`).pipe(timeout(this.TIMEOUT_MS))
    );
  }

  async generateWebhook(): Promise<{ webhook_url: string, auth_header: string }> {
    return firstValueFrom(
      this.http.post<{ webhook_url: string, auth_header: string }>(`${this.apiUrl}/webhook/generate`, {}).pipe(timeout(this.TIMEOUT_MS))
    );
  }

  async revokeWebhook(): Promise<void> {
    await firstValueFrom(
      this.http.delete(`${this.apiUrl}/webhook`).pipe(timeout(this.TIMEOUT_MS))
    );
  }
}
