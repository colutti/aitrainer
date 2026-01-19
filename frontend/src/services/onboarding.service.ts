import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';
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
    } catch (error: any) {
      // Handle HTTP errors (404, 410, 409)
      if (error.error?.detail) {
        return error.error.detail;
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
