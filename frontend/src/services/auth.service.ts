import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';
import { ChatService } from './chat.service';

/**
 * Service responsible for user authentication.
 * Manages JWT tokens storage and login state using Angular signals.
 */
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  /** Signal indicating whether the user is currently authenticated */
  isAuthenticated = signal<boolean>(false);

  /** Local storage key for storing the JWT token */
  private tokenKey = 'jwt_token';

  constructor(private http: HttpClient, private chatService: ChatService) {
    // Check for a stored JWT token to maintain login state across page refreshes
    const token = localStorage.getItem(this.tokenKey);
    if (token) {
      this.isAuthenticated.set(true);
    }
  }

  /**
   * Attempts to authenticate a user with email and password.
   * On success, stores the JWT token and updates authentication state.
   * @param email - User's email address
   * @param password - User's password
   * @returns Promise resolving to true if login successful, false otherwise
   */
  async login(email: string, password: string): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.http.post<{ token: string }>(`${environment.apiUrl}/user/login`, { email, password })
      );
      if (response && response.token) {
        localStorage.setItem(this.tokenKey, response.token);
        this.isAuthenticated.set(true);
        return true;
      }
      this.isAuthenticated.set(false);
      return false;
    } catch {
      this.isAuthenticated.set(false);
      return false;
    }
  }

  /**
   * Logs out the current user.
   * Clears chat history, removes stored token, and updates authentication state.
   */
  logout(): void {
    this.chatService.clearHistory();
    this.isAuthenticated.set(false);
    localStorage.removeItem(this.tokenKey);
  }

  /**
   * Retrieves the stored JWT token.
   * @returns The JWT token string or null if not authenticated
   */
  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }
}

