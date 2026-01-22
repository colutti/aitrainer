import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { TrainerProfile, TrainerCard } from '../models/trainer-profile.model';
import { catchError, of, firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TrainerProfileService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/trainer`;

  // Default fallback if nothing is loaded
  private readonly DEFAULT_PROFILE: TrainerProfile = {
    trainer_type: 'atlas'
  };

  constructor() {}

  getAvailableTrainers(): Promise<TrainerCard[]> {
    return firstValueFrom(this.http.get<TrainerCard[]>(`${this.apiUrl}/available_trainers`));
  }

  async fetchProfile(): Promise<TrainerProfile> {
    try {
      const profile = await firstValueFrom(
        this.http.get<TrainerProfile>(`${this.apiUrl}/trainer_profile`).pipe(
          catchError(err => {
            console.warn('Failed to fetch trainer profile, using default', err);
            return of(this.DEFAULT_PROFILE);
          })
        )
      );
      return (profile && profile.trainer_type) ? profile : this.DEFAULT_PROFILE;
    } catch {
      return this.DEFAULT_PROFILE;
    }
  }

  updateProfile(profile: TrainerProfile): Promise<TrainerProfile> {
    return firstValueFrom(this.http.put<TrainerProfile>(`${this.apiUrl}/update_trainer_profile`, profile));
  }
}