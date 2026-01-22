import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';

export interface OnboardingData {
  token: string;
  password: string;
  gender: 'Masculino' | 'Feminino';
  age: number;
  weight: number;
  height: number;
  goal_type: 'lose' | 'gain' | 'maintain';
  weekly_rate: number;
  trainer_type: 'atlas' | 'luna' | 'sargento' | 'sofia';
}

export interface ValidateResponse {
  valid: boolean;
  email?: string;
  reason?: string;
}

export interface CompleteResponse {
  token: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class OnboardingService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/onboarding`;

  async validateToken(token: string): Promise<ValidateResponse> {
    try {
      return await firstValueFrom(
        this.http.get<ValidateResponse>(`${this.apiUrl}/validate`, {
          params: { token }
        })
      );
    } catch (error: unknown) {
      // Handle HTTP errors (404, 410, 409)
      const err = error as { error?: { detail?: ValidateResponse } };
      if (err.error?.detail) {
        return err.error.detail;
      }
      throw error;
    }
  }

  async completeOnboarding(data: OnboardingData): Promise<CompleteResponse> {
    return await firstValueFrom(
      this.http.post<CompleteResponse>(`${this.apiUrl}/complete`, data)
    );
  }
}
