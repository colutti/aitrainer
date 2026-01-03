import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environment';
import { Memory, MemoryListResponse } from '../models/memory.model';

/**
 * Service responsible for managing user memories with pagination.
 * Handles fetching, navigating pages, and deleting memory records.
 */
@Injectable({
  providedIn: 'root',
})
export class MemoryService {
  /** Signal containing the list of memories */
  memories = signal<Memory[]>([]);

  /** Signal indicating if memories are being loaded */
  isLoading = signal(false);

  /** Current page number (1-indexed) */
  currentPage = signal(1);

  /** Number of items per page */
  pageSize = signal(10);

  /** Total number of pages */
  totalPages = signal(0);

  /** Total number of memories */
  totalMemories = signal(0);

  constructor(private http: HttpClient) {}

  /**
   * Fetches paginated memories for the current user.
   * @param page - Page number to fetch (default: current page)
   * @returns Promise resolving to the list of memories
   */
  async getMemories(page: number = this.currentPage()): Promise<Memory[]> {
    this.isLoading.set(true);
    try {
      const params = new HttpParams()
        .set('page', page.toString())
        .set('page_size', this.pageSize().toString());

      const response = await firstValueFrom(
        this.http.get<MemoryListResponse>(`${environment.apiUrl}/memory/list`, { params })
      );

      this.memories.set(response.memories);
      this.currentPage.set(response.page);
      this.totalPages.set(response.total_pages);
      this.totalMemories.set(response.total);

      return response.memories;
    } catch {
      return [];
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Navigates to the next page of memories.
   */
  async nextPage(): Promise<void> {
    if (this.currentPage() < this.totalPages()) {
      await this.getMemories(this.currentPage() + 1);
    }
  }

  /**
   * Navigates to the previous page of memories.
   */
  async previousPage(): Promise<void> {
    if (this.currentPage() > 1) {
      await this.getMemories(this.currentPage() - 1);
    }
  }

  /**
   * Deletes a specific memory and reloads the current page.
   * @param memoryId - The ID of the memory to delete
   */
  async deleteMemory(memoryId: string): Promise<void> {
    await firstValueFrom(
      this.http.delete(`${environment.apiUrl}/memory/${memoryId}`)
    );
    // Reload current page to get updated list
    await this.getMemories(this.currentPage());
  }
}

