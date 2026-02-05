import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { ImportResult } from '../models/integration.model';

@Injectable({
  providedIn: 'root'
})
export class ImportService {
  private apiUrl = `${environment.apiUrl}/nutrition/import`;

  constructor(private http: HttpClient) {}

  async uploadMyFitnessPalCSV(file: File): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    return firstValueFrom(
      this.http.post<ImportResult>(`${this.apiUrl}/myfitnesspal`, formData)
    );
  }
}
