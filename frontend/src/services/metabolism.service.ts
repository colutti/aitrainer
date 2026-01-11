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
      const data = await firstValueFrom(
        this.http.get<MetabolismResponse>(`${environment.apiUrl}/metabolism/summary?weeks=${weeks}`)
      );
      this.stats.set(data);
    } catch (error) {
      console.error('Failed to fetch metabolism summary', error);
      // Retrieve empty/error state if needed, or handle error
      this.stats.set(null);
    } finally {
      this.isLoading.set(false);
    }
  }
}
