import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { Workout, WorkoutListResponse } from '../models/workout.model';
import { WorkoutStats } from '../models/stats.model';

/**
 * Service for managing workout logs with pagination.
 */
@Injectable({
  providedIn: 'root',
})
export class WorkoutService {
  workouts = signal<Workout[]>([]);
  isLoading = signal(false);
  currentPage = signal(1);
  pageSize = signal(10);
  totalPages = signal(0);
  totalWorkouts = signal(0);
  selectedType = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  /**
   * Fetches paginated workouts for the current user.
   */
  async getWorkouts(page: number = 1, type: string | null = this.selectedType()): Promise<Workout[]> {
    this.isLoading.set(true);
    // If type changed or explicitly passed, update signal
    if (type !== this.selectedType()) {
         this.selectedType.set(type);
    }

    try {
      let params = new HttpParams()
        .set('page', page.toString())
        .set('page_size', this.pageSize().toString());
      
      if (type) {
        params = params.set('workout_type', type);
      }

      const response = await firstValueFrom(
        this.http.get<WorkoutListResponse>(`${environment.apiUrl}/workout/list`, { params })
      );

      this.workouts.set(response.workouts);
      this.currentPage.set(response.page);
      this.totalPages.set(response.total_pages);
      this.totalWorkouts.set(response.total);

      return response.workouts;
    } catch (error) {
      console.error('Error fetching workouts:', error);
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  async getTypes(): Promise<string[]> {
    try {
        return await firstValueFrom(this.http.get<string[]>(`${environment.apiUrl}/workout/types`));
    } catch (error) {
        console.error('Error fetching types:', error);
        return [];
    }
  }



  async getStats(): Promise<WorkoutStats> {
      return await firstValueFrom(this.http.get<WorkoutStats>(`${environment.apiUrl}/workout/stats`));
  }

  async nextPage(): Promise<void> {
    if (this.currentPage() < this.totalPages()) {
      await this.getWorkouts(this.currentPage() + 1);
    }
  }

  async previousPage(): Promise<void> {
    if (this.currentPage() > 1) {
      await this.getWorkouts(this.currentPage() - 1);
    }
  }

  /**
   * Deletes a workout log and reloads the list.
   */
  async deleteWorkout(workoutId: string): Promise<void> {
    await firstValueFrom(this.http.delete(`${environment.apiUrl}/workout/${workoutId}`));
    await this.getWorkouts(this.currentPage());
  }
}
