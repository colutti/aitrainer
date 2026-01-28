import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { UserProfile } from '../models/user-profile.model';
import { UserProfileInput } from '../models/user-profile-input.model';

/**
 * Service responsible for managing user profile data.
 * Handles fetching and updating user profile information.
 */
@Injectable({
  providedIn: 'root',
})
export class UserProfileService {
  /** Signal containing the current user profile, or null if not loaded */
  userProfile = signal<UserProfile | null>(null);

  constructor(private http: HttpClient) { }

  /**
   * Fetches the user profile from the backend.
   * @returns Promise resolving to the UserProfile or null on error
   */
  async getProfile(): Promise<UserProfile | null> {
    try {
      const profile = await firstValueFrom(
        this.http.get<UserProfile>(`${environment.apiUrl}/user/profile`)
      );
      this.userProfile.set(profile);
      return profile;
    } catch {
      return null;
    }
  }

  /**
   * Updates the user profile on the backend.
   * On validation errors (422), throws the error details for component handling.
   * @param profile - The profile data to update
   * @throws Validation error details on 422, or generic error on other failures
   */
  async updateProfile(profile: UserProfileInput): Promise<void> {
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/user/update_profile`, profile)
      );
      this.userProfile.update(currentProfile => {
        if (!currentProfile) {
          return profile as UserProfile;
        }
        return { ...currentProfile, ...profile };
      });
    } catch (error: unknown) {
      if (error instanceof HttpErrorResponse && error.status === 422) {
        throw error.error.detail;
      }
      throw new Error('An unexpected error occurred.');
    }
  }
}

