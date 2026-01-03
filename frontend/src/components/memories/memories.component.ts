import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MemoryService } from '../../services/memory.service';
import { Memory } from '../../models/memory.model';

/**
 * Component for displaying and managing user memories with pagination.
 * Shows paginated memories with navigation and delete functionality.
 */
@Component({
  selector: 'app-memories',
  templateUrl: './memories.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule]
})
export class MemoriesComponent implements OnInit {
  private memoryService = inject(MemoryService);

  memories = this.memoryService.memories;
  isLoading = this.memoryService.isLoading;
  currentPage = this.memoryService.currentPage;
  totalPages = this.memoryService.totalPages;
  totalMemories = this.memoryService.totalMemories;
  deletingId = signal<string | null>(null);
  showDeleteSuccess = signal(false);

  async ngOnInit(): Promise<void> {
    await this.memoryService.getMemories(1);
  }

  /**
   * Navigates to the previous page.
   */
  async previousPage(): Promise<void> {
    await this.memoryService.previousPage();
  }

  /**
   * Navigates to the next page.
   */
  async nextPage(): Promise<void> {
    await this.memoryService.nextPage();
  }

  /**
   * Deletes a memory after user confirmation.
   * The service automatically reloads the current page.
   * @param memory - The memory to delete
   */
  async deleteMemory(memory: Memory): Promise<void> {
    const confirmed = confirm('Tem certeza que deseja excluir esta memória?');
    if (!confirmed) {
      return;
    }

    this.deletingId.set(memory.id);
    try {
      await this.memoryService.deleteMemory(memory.id);
      this.showDeleteSuccess.set(true);
      setTimeout(() => this.showDeleteSuccess.set(false), 2000);
    } finally {
      this.deletingId.set(null);
    }
  }

  /**
   * Formats a date string to Brazilian locale format.
   * @param dateStr - ISO date string or null
   * @returns Formatted date string
   */
  formatDate(dateStr: string | null): string {
    if (!dateStr) return 'Data desconhecida';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Data inválida';
    }
  }
}

