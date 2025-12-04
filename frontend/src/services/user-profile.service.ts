
import { Injectable, signal } from '@angular/core';
import { UserProfile } from '../models/user-profile.model';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../environment';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class UserProfileService {
  userProfile = signal<UserProfile | null>(null);

  constructor(private http: HttpClient, private auth: AuthService) { }

  getProfile(): Promise<UserProfile | null> {
    return this.http.get<UserProfile>(`${environment.apiUrl}/profile`)
      .toPromise()
      .then(profile => {
        this.userProfile.set(profile);
        return profile;
      })
      .catch(() => null);
  }

  updateProfile(profile: UserProfile): Promise<boolean> {
    return this.http.post<UserProfile>(`${environment.apiUrl}/update_profile`, profile)
      .toPromise()
      .then(updated => {
        this.userProfile.set(updated);
        return true;
      })
      .catch(() => false);
  }
}
