import { Injectable } from '@angular/core';
import { signal } from '@angular/core';

export interface PaginationState {
  currentPage: number;
  totalPages: number;
  pageSize: number;
}

@Injectable({ providedIn: 'root' })
export class PaginationService {
  private currentPage = signal(1);
  private totalPages = signal(1);
  private pageSize = signal(10);

  getCurrentPage() {
    return this.currentPage.asReadonly();
  }

  getTotalPages() {
    return this.totalPages.asReadonly();
  }

  getPageSize() {
    return this.pageSize.asReadonly();
  }

  setPageSize(size: number) {
    this.pageSize.set(size);
  }

  setTotalPages(total: number) {
    this.totalPages.set(total);
  }

  nextPage() {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(p => p + 1);
    }
  }

  prevPage() {
    if (this.currentPage() > 1) {
      this.currentPage.update(p => p - 1);
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
    }
  }

  reset() {
    this.currentPage.set(1);
  }

  getState(): PaginationState {
    return {
      currentPage: this.currentPage(),
      totalPages: this.totalPages(),
      pageSize: this.pageSize()
    };
  }
}
