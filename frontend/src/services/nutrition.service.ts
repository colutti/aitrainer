import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../environment';
import { Observable, tap } from 'rxjs';
import { NutritionListResponse, NutritionStats } from '../models/nutrition.model';

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
  getLogs(page: number = 1, pageSize: number = 10, days?: number): Observable<NutritionListResponse> {
    let params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    if (days) {
      params = params.set('days', days);
    }

    return this.http.get<NutritionListResponse>(`${this.apiUrl}/list`, { params });
  }

  /**
   * Fetches nutrition stats for the dashboard.
   * Updates the local signal automatically.
   */
  getStats(): Observable<NutritionStats> {
    return this.http.get<NutritionStats>(`${this.apiUrl}/stats`).pipe(
      tap(stats => this.stats.set(stats))
    );
  }

  /**
   * Fetches today's nutrition log specifically.
   */
  getTodayLog(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/today`);
  }
}
