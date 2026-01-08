import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { TrainerProfile, TrainerCard } from '../models/trainer-profile.model';
import { tap, catchError, of } from 'rxjs';

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
    return new Promise((resolve, reject) => {
      this.http.get<TrainerCard[]>(`${this.apiUrl}/available_trainers`)
        .subscribe({
          next: (data) => resolve(data),
          error: (err) => reject(err)
        });
    });
  }

  fetchProfile(): Promise<TrainerProfile> {
    return new Promise((resolve, reject) => {
      this.http.get<TrainerProfile>(`${this.apiUrl}/trainer_profile`)
        .pipe(
          catchError(err => {
            console.warn('Failed to fetch trainer profile, using default', err);
            // Check legacy local storage as fallback
            const legacyName = localStorage.getItem('trainer_name'); 
            if (legacyName) {
               // Silently migrate via default logic on backend next save
               // or just return default 'atlas' for new UI
            }
            return of(this.DEFAULT_PROFILE);
          })
        )
        .subscribe({
          next: (profile) => {
            // Ensure we have a valid structure
            if (!profile || !profile.trainer_type) {
                profile = this.DEFAULT_PROFILE;
            }
            resolve(profile);
          },
          error: (err) => resolve(this.DEFAULT_PROFILE)
        });
    });
  }

  updateProfile(profile: TrainerProfile): Promise<TrainerProfile> {
    return new Promise((resolve, reject) => {
      this.http.put<TrainerProfile>(`${this.apiUrl}/update_trainer_profile`, profile)
        .subscribe({
          next: (updated) => resolve(updated),
          error: (err) => reject(err)
        });
    });
  }
}