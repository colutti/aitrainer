import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';
import { TokenExpirationService } from './token-expiration.service';


export interface UserInfo {
  email: string;
  role: 'user' | 'admin';
}

export const AUTH_TOKEN_KEY = 'jwt_token';

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

  /** Signal indicating whether the user is an admin */
  isAdmin = signal<boolean>(false);

  /** Signal containing user information */
  userInfo = signal<UserInfo | null>(null);

  /** Signal indicating whether user info is being loaded */
  isLoadingUserInfo = signal<boolean>(false);

  /** Signal indicating whether authentication is being checked on app initialization */
  isCheckingAuth = signal<boolean>(false);

  constructor(
    private http: HttpClient,
    private tokenExpirationService: TokenExpirationService
  ) {
    // Check for a stored JWT token to maintain login state across page refreshes
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      // Don't set isAuthenticated immediately - wait for validation
      this.isCheckingAuth.set(true);
      // Validate token by loading user info
      this.loadUserInfo().finally(() => {
        this.isCheckingAuth.set(false);
      });
    }
  }

  async loadUserInfo(): Promise<void> {
    this.isLoadingUserInfo.set(true);
    try {
      const info = await firstValueFrom(
        this.http.get<UserInfo>(`${environment.apiUrl}/user/me`)
      );
      // Token is valid - set authenticated state
      this.isAuthenticated.set(true);
      this.userInfo.set(info);
      this.isAdmin.set(info.role === 'admin');

      // Start monitoring token expiration
      const token = this.getToken();
      if (token) {
        this.tokenExpirationService.startMonitoring(token);
      }
    } catch (error) {
      console.error('Failed to load user info:', error);
      this.isAdmin.set(false);
      this.userInfo.set(null);
      // If user info fails to load, token might be invalid
      this.isAuthenticated.set(false);
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } finally {
      this.isLoadingUserInfo.set(false);
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
        localStorage.setItem(AUTH_TOKEN_KEY, response.token);
        // Start monitoring token expiration
        this.tokenExpirationService.startMonitoring(response.token);
        this.isAuthenticated.set(true);
        await this.loadUserInfo();
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
  async logout(): Promise<void> {
    try {
      if (this.isAuthenticated()) {
        await firstValueFrom(this.http.post(`${environment.apiUrl}/user/logout`, {}));
      }
    } catch (error) {
      console.error('Logout failed on backend:', error);
    } finally {
      // Stop monitoring token expiration
      this.tokenExpirationService.stopMonitoring();
      // Clear all authentication state
      this.isAuthenticated.set(false);
      this.isAdmin.set(false);
      this.userInfo.set(null);
      this.isLoadingUserInfo.set(false);
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  }

  /**
   * Retrieves the stored JWT token.
   * @returns The JWT token string or null if not authenticated
   */
  getToken(): string | null {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }
}

