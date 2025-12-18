
import { Injectable, signal } from '@angular/core';
import { UserProfile } from '../models/user-profile.model';
import { UserProfileInput } from '../models/user-profile-input.model';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { environment } from '../environment';
import { AuthService } from './auth.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UserProfileService {
  userProfile = signal<UserProfile | null>(null);

  constructor(private http: HttpClient, private auth: AuthService) { }

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

  async updateProfile(profile: UserProfileInput): Promise<void> {
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/user/update_profile`, profile)
      );
      this.userProfile.update(currentProfile => {
        if (!currentProfile) {
            // This case should ideally not be hit if a profile is loaded before update is possible.
            // We create a new object asserting email exists, though it would be null.
            return { ...profile, email: '' }; 
        }
        return { ...currentProfile, ...profile };
      });
    } catch (error: any) {
      // Re-throw the error to be caught by the component
      if (error instanceof HttpErrorResponse && error.status === 422) {
        throw error.error.detail;
      }
      throw new Error('An unexpected error occurred.');
    }
  }
}
