import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';

export interface TelegramStatus {
  linked: boolean;
  telegram_username?: string;
  linked_at?: string;
  telegram_notify_on_workout?: boolean;
  telegram_notify_on_nutrition?: boolean;
  telegram_notify_on_weight?: boolean;
}

export interface LinkingCode {
  code: string;
  expires_in_seconds: number;
}

export interface TelegramNotificationSettings {
  telegram_notify_on_workout?: boolean;
  telegram_notify_on_nutrition?: boolean;
  telegram_notify_on_weight?: boolean;
}

@Injectable({ providedIn: 'root' })
export class TelegramService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/telegram`;

  async generateCode(): Promise<LinkingCode> {
    return firstValueFrom(
      this.http.post<LinkingCode>(`${this.baseUrl}/generate-code`, {})
    );
  }

  async getStatus(): Promise<TelegramStatus> {
    return firstValueFrom(
      this.http.get<TelegramStatus>(`${this.baseUrl}/status`)
    );
  }

  async unlink(): Promise<void> {
    await firstValueFrom(
      this.http.post(`${this.baseUrl}/unlink`, {})
    );
  }

  async updateNotifications(settings: TelegramNotificationSettings): Promise<void> {
    const userUrl = `${environment.apiUrl}/user`;
    await firstValueFrom(
      this.http.post(`${userUrl}/telegram-notifications`, settings)
    );
  }
}
