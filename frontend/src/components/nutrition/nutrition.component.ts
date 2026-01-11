import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NutritionService } from '../../services/nutrition.service';
import { NutritionLog } from '../../models/nutrition.model';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-nutrition',
  standalone: true,
  imports: [CommonModule, SkeletonComponent],
  templateUrl: './nutrition.component.html',
})
export class NutritionComponent implements OnInit {
  private nutritionService = inject(NutritionService);

  logs = signal<NutritionLog[]>([]);
  isLoading = signal(true);
  currentPage = signal(1);
  totalPages = signal(1);
  totalLogs = signal(0);
  
  // Filtering (optional for now, but UI shows dropdown)
  daysFilter = signal<number | undefined>(undefined);

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    this.isLoading.set(true);
    this.nutritionService.getLogs(this.currentPage(), 10, this.daysFilter())
      .subscribe({
        next: (response) => {
          this.logs.set(response.logs);
          this.totalPages.set(response.total_pages);
          this.totalLogs.set(response.total);
          this.isLoading.set(false);
        },
        error: (err) => {
          console.error('Failed to load nutrition logs', err);
          this.isLoading.set(false);
        }
      });
  }

  nextPage() {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(p => p + 1);
      this.loadLogs();
    }
  }

  prevPage() {
    if (this.currentPage() > 1) {
      this.currentPage.update(p => p - 1);
      this.loadLogs();
    }
  }

  // Helpers for template
  getMacroPercentage(grams: number, type: 'protein' | 'carbs' | 'fat', calories: number): string {
    if (!calories) return '0%';
    const caloriesPerGram = type === 'fat' ? 9 : 4;
    const percentage = Math.round(((grams * caloriesPerGram) / calories) * 100);
    return `${percentage}%`;
  }

  getFormattedDate(dateStr: string): string {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      // Format: "domingo, 11 de janeiro de 2026"
      return new Intl.DateTimeFormat('pt-BR', { 
        weekday: 'long',
        day: 'numeric', 
        month: 'long',
        year: 'numeric'
      }).format(date);
    } catch (e) {
      return dateStr;
    }
  }
}
