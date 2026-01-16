import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { MetabolismResponse } from '../models/metabolism.model';

@Injectable({
  providedIn: 'root',
})
export class MetabolismService {
  stats = signal<MetabolismResponse | null>(null);
  isLoading = signal<boolean>(false);
  
  constructor(private http: HttpClient) {}

  async fetchSummary(weeks: number = 3): Promise<void> {
    this.isLoading.set(true);
    try {
      const data = await this.getSummary(weeks);
      this.stats.set(data);
    } catch (error) {
      console.error('Failed to fetch metabolism summary', error);
      this.stats.set(null);
    } finally {
      this.isLoading.set(false);
    }
  }

  async getSummary(weeks: number = 3): Promise<MetabolismResponse> {
    return firstValueFrom(
      this.http.get<MetabolismResponse>(`${environment.apiUrl}/metabolism/summary?weeks=${weeks}`)
    );
  }
  async getInsightStream(weeks: number = 3): Promise<ReadableStreamDefaultReader<Uint8Array>> {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(`${environment.apiUrl}/metabolism/insight?weeks=${weeks}`, {
          headers: {
              'Authorization': `Bearer ${token}`
          }
      });
      
      if (!response.body) {
          throw new Error('No ReadableStream');
      }

      const reader = response.body.getReader();
      return reader;
  }
}
