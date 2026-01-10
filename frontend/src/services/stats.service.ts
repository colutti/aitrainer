import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { WorkoutStats } from '../models/stats.model';

@Injectable({
  providedIn: 'root',
})
export class StatsService {
  stats = signal<WorkoutStats | null>(null);
  isLoading = signal(false);

  constructor(private http: HttpClient) {}

  async fetchStats(): Promise<void> {
    this.isLoading.set(true);
    try {
      const data = await firstValueFrom(
        this.http.get<WorkoutStats>(`${environment.apiUrl}/workout/stats`)
      );
      this.stats.set(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      this.isLoading.set(false);
    }
  }
}
