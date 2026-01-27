import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../environment';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  // ==================
  // Users
  // ==================

  async listUsers(page: number, pageSize: number, search?: string) {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (search) {
      params = params.set('search', search);
    }

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/users/list`, { params })
    );
  }

  async getUserDetails(email: string) {
    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/users/${email}/details`)
    );
  }

  async updateUser(email: string, updates: any) {
    return firstValueFrom(
      this.http.patch<any>(`${this.apiUrl}/admin/users/${email}`, updates)
    );
  }

  async deleteUser(email: string) {
    return firstValueFrom(
      this.http.delete<any>(`${this.apiUrl}/admin/users/${email}`)
    );
  }

  // ==================
  // Logs
  // ==================

  async getApplicationLogs(limit: number, level?: string) {
    let params = new HttpParams().set('limit', limit.toString());

    if (level) {
      params = params.set('level', level);
    }

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/logs/application`, { params })
    );
  }

  async getBetterStackLogs(limit: number, query?: string) {
    let params = new HttpParams().set('limit', limit.toString());

    if (query) {
      params = params.set('query', query);
    }

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/logs/betterstack`, { params })
    );
  }

  // ==================
  // Prompts
  // ==================

  async listPrompts(page: number, pageSize: number, userEmail?: string) {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (userEmail) {
      params = params.set('user_email', userEmail);
    }

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/prompts/list`, { params })
    );
  }

  async getPromptDetails(promptId: string) {
    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/prompts/${promptId}`)
    );
  }

  // ==================
  // Memory & Messages
  // ==================

  async getUserMessages(userEmail: string, limit: number = 50) {
    const params = new HttpParams().set('limit', limit.toString());

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/memory/${userEmail}/messages`, { params })
    );
  }

  async getUserMemories(userEmail: string, page: number = 1, pageSize: number = 20) {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/memory/${userEmail}/memories`, { params })
    );
  }

  // ==================
  // Analytics
  // ==================

  async getOverview() {
    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/analytics/overview`)
    );
  }

  async getQualityMetrics() {
    return firstValueFrom(
      this.http.get<any>(`${this.apiUrl}/admin/analytics/quality-metrics`)
    );
  }
}
