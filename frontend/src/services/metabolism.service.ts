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
  
  // Hero Insight Cache
  insightText = signal<string>('');
  isInsightLoading = signal<boolean>(false);
  
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
  async generateInsight(weeks: number = 3, force: boolean = false): Promise<void> {
      if ((this.insightText() && !force) || this.isInsightLoading()) return;

      this.isInsightLoading.set(true);
      if (force) this.insightText.set('');

      try {
          const reader = await this.getInsightStream(weeks, force);
          const decoder = new TextDecoder();

          while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              this.insightText.update(prev => prev + chunk);
          }
      } catch (error) {
          console.error("Stream error", error);
          if (!this.insightText()) {
             this.insightText.set("Não foi possível gerar a análise do treinador no momento.");
          }
      } finally {
          this.isInsightLoading.set(false);
      }
  }

  async getInsightStream(weeks: number = 3, force: boolean = false): Promise<ReadableStreamDefaultReader<Uint8Array>> {
      const token = localStorage.getItem('jwt_token');
      const url = `${environment.apiUrl}/metabolism/insight?weeks=${weeks}${force ? '&force=true' : ''}`;
      const response = await fetch(url, {
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
