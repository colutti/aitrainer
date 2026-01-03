import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { Memory, MemoryListResponse } from '../models/memory.model';

/**
 * Service responsible for managing user memories.
 * Handles fetching and deleting memory records.
 */
@Injectable({
  providedIn: 'root',
})
export class MemoryService {
  /** Signal containing the list of memories */
  memories = signal<Memory[]>([]);

  /** Signal indicating if memories are being loaded */
  isLoading = signal(false);

  constructor(private http: HttpClient) {}

  /**
   * Fetches all memories for the current user.
   * @returns Promise resolving to the list of memories
   */
  async getMemories(): Promise<Memory[]> {
    this.isLoading.set(true);
    try {
      const response = await firstValueFrom(
        this.http.get<MemoryListResponse>(`${environment.apiUrl}/memory/list`)
      );
      this.memories.set(response.memories);
      return response.memories;
    } catch {
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Deletes a specific memory.
   * @param memoryId - The ID of the memory to delete
   */
  async deleteMemory(memoryId: string): Promise<void> {
    await firstValueFrom(
      this.http.delete(`${environment.apiUrl}/memory/${memoryId}`)
    );
    this.memories.update(memories =>
      memories.filter(m => m.id !== memoryId)
    );
  }
}
