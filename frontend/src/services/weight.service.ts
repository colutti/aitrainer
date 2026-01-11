import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { WeightLog } from '../models/weight-log.model';

@Injectable({
  providedIn: 'root',
})
export class WeightService {
  /** Check if saved recently to show feedback */
  lastSaved = signal<boolean>(false);

  constructor(private http: HttpClient) { }

  /**
   * Logs a new weight entry.
   */
  async logWeight(weight: number): Promise<void> {
    const today = new Date().toISOString().split('T')[0];
    const log: Partial<WeightLog> = {
      weight_kg: weight,
      date: today
    };

    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/weight`, log)
      );
      this.lastSaved.set(true);
      setTimeout(() => this.lastSaved.set(false), 3000);
    } catch (error) {
      console.error('Failed to log weight', error);
      throw error;
    }
  }

  /**
   * Gets weight history.
   */
  async getHistory(): Promise<WeightLog[]> {
    try {
      return await firstValueFrom(
        this.http.get<WeightLog[]>(`${environment.apiUrl}/weight?limit=30`)
      );
    } catch {
      return [];
    }
  }
}
