
import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  isAuthenticated = signal<boolean>(false);

  private tokenKey = 'jwt_token';


  constructor(private http: HttpClient) {
    // Check for a stored JWT token to maintain login state
    const token = localStorage.getItem(this.tokenKey);
    if (token) {
      this.isAuthenticated.set(true);
    }
  }


  async login(email: string, password: string): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.http.post<{ token: string }>(`${environment.apiUrl}/login`, { email, password })
      );
      if (response && response.token) {
        localStorage.setItem(this.tokenKey, response.token);
        this.isAuthenticated.set(true);
        return true;
      }
      this.isAuthenticated.set(false);
      return false;
    } catch (error) {
      this.isAuthenticated.set(false);
      return false;
    }
  }

  logout(): void {
    this.isAuthenticated.set(false);
    localStorage.removeItem(this.tokenKey);
    // Optionally, call backend logout endpoint if needed
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }
}
