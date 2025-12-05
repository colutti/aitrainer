
import { Injectable, signal } from '@angular/core';
import { UserProfile } from '../models/user-profile.model';
import { HttpClient, HttpHeaders } from '@angular/common/http';
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
        this.http.get<UserProfile>(`${environment.apiUrl}/profile`)
      );
      this.userProfile.set(profile);
      return profile;
    } catch {
      return null;
    }
  }

  async updateProfile(profile: UserProfile): Promise<boolean> {
    try {
      const updated = await firstValueFrom(
        this.http.post<UserProfile>(`${environment.apiUrl}/update_profile`, profile)
      );
      this.userProfile.set(updated);
      return true;
    } catch {
      return false;
    }
  }
}
