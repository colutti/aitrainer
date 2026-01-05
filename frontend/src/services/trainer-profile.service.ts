import { Injectable, signal, effect } from '@angular/core';
import { TrainerProfile } from '../models/trainer-profile.model';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';

/** Default trainer profile configuration */
const DEFAULT_TRAINER_PROFILE: TrainerProfile = {
  name: 'Atlas',
  gender: 'Masculino',

  style: 'Científico',
};

/**
 * Service responsible for managing the AI trainer's profile and personality.
 * Handles profile persistence to localStorage and synchronization with backend.
 */
@Injectable({
  providedIn: 'root',
})
export class TrainerProfileService {
  /** Signal containing the current trainer profile */
  trainerProfile = signal<TrainerProfile>(DEFAULT_TRAINER_PROFILE);

  constructor(private http: HttpClient) {
    // Load profile from localStorage if available
    const storedProfile = localStorage.getItem('trainer_profile');
    if (storedProfile) {
      const parsed: TrainerProfile = JSON.parse(storedProfile);
      // Fill empty fields with default values
      this.trainerProfile.set({
        name: parsed.name || DEFAULT_TRAINER_PROFILE.name,
        gender: parsed.gender || DEFAULT_TRAINER_PROFILE.gender,

        style: parsed.style || DEFAULT_TRAINER_PROFILE.style,
      });
    }

    // Automatically persist profile changes to localStorage
    effect(() => {
      localStorage.setItem('trainer_profile', JSON.stringify(this.trainerProfile()));
    });
  }

  /**
   * Saves the trainer profile to the backend.
   * @param profile - The trainer profile to save
   * @returns Promise resolving to true if successful, false otherwise
   */
  async updateProfile(profile: TrainerProfile): Promise<void> {
    await firstValueFrom(this.http.post(`${environment.apiUrl}/trainer/update_trainer_profile`, profile));
    this.trainerProfile.set(profile);
  }

  /**
   * Fetches the trainer profile from the backend.
   * Updates the local signal on success.
   */
  async fetchProfile(): Promise<void> {
    try {
      const profile = await firstValueFrom(
        this.http.get<TrainerProfile>(`${environment.apiUrl}/trainer/trainer_profile`)
      );
      this.trainerProfile.set(profile);
    } catch (err) {
      console.error('Error fetching trainer profile:', err);
    }
  }

  /**
   * Returns the current trainer profile.
   * @returns The current TrainerProfile object
   */
  getProfile(): TrainerProfile {
    return this.trainerProfile();
  }
}