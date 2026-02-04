import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';
import { NutritionLog, NutritionListResponse, NutritionStats } from '../models/nutrition.model';

@Injectable({
  providedIn: 'root'
})
export class NutritionService {
  private apiUrl = `${environment.apiUrl}/nutrition`;

  // Signals for storing state (optional but good for reactive UI)
  stats = signal<NutritionStats | null>(null);

  constructor(private http: HttpClient) {}

  /**
   * Fetches nutrition logs with pagination.
   */
  async getLogs(page: number = 1, pageSize: number = 10, days?: number): Promise<NutritionListResponse> {
    let params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    if (days) {
      params = params.set('days', days);
    }

    return firstValueFrom(this.http.get<NutritionListResponse>(`${this.apiUrl}/list`, { params }));
  }

  /**
   * Fetches nutrition stats for the dashboard.
   * Updates the local signal automatically.
   */
  async getStats(): Promise<NutritionStats> {
    const stats = await firstValueFrom(this.http.get<NutritionStats>(`${this.apiUrl}/stats`));
    this.stats.set(stats);
    return stats;
  }

  /**
   * Fetches today's nutrition log specifically.
   */
  async getTodayLog(): Promise<NutritionLog | null> {
    return firstValueFrom(this.http.get<NutritionLog | null>(`${this.apiUrl}/today`));
  }

  /**
   * Creates a new nutrition log.
   */
  async logNutrition(data: {
    date: string;
    source: string;
    calories: number;
    protein_grams: number;
    carbs_grams: number;
    fat_grams: number;
    fiber_grams?: number;
    sodium_mg?: number;
  }): Promise<NutritionLog> {
    return firstValueFrom(this.http.post<NutritionLog>(`${this.apiUrl}/log`, data));
  }

  /**
   * Deletes a nutrition log.
   */
  async deleteLog(logId: string): Promise<any> {
    return firstValueFrom(this.http.delete(`${this.apiUrl}/${logId}`));
  }
}
