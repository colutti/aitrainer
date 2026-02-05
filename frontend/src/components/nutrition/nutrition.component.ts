import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NutritionService } from '../../services/nutrition.service';
import { MetabolismService } from '../../services/metabolism.service';
import { NutritionLog, NutritionStats } from '../../models/nutrition.model';
import { AppDateFormatPipe } from '../../pipes/date-format.pipe';
import { SkeletonComponent } from '../skeleton/skeleton.component';
import { WidgetMacrosTodayComponent } from '../widgets/widget-macros-today.component';
import { WidgetAdherenceComponent } from '../widgets/widget-adherence.component';
import { WidgetCaloriesWeightComparisonComponent } from '../widgets/widget-calories-weight-comparison.component';
import { WidgetMacroTargetsComponent } from '../widgets/widget-macro-targets.component';
import { WidgetCalorieHistoryComponent } from '../widgets/nutrition/widget-calorie-history.component';
import { WidgetCalorieVolatilityComponent } from '../widgets/nutrition/widget-calorie-volatility.component';
import { WidgetAverageCaloriesComponent } from '../widgets/nutrition/widget-average-calories.component';

@Component({
  selector: 'app-nutrition',
  standalone: true,
  imports: [CommonModule, AppDateFormatPipe, SkeletonComponent, WidgetMacrosTodayComponent, WidgetAdherenceComponent, WidgetCaloriesWeightComparisonComponent, WidgetMacroTargetsComponent, WidgetCalorieHistoryComponent, WidgetCalorieVolatilityComponent, WidgetAverageCaloriesComponent],
  templateUrl: './nutrition.component.html',
})
export class NutritionComponent implements OnInit {
  private nutritionService = inject(NutritionService);
  public metabolismService = inject(MetabolismService);

  logs = signal<NutritionLog[]>([]);
  isLoading = signal(true);
  currentPage = signal(1);
  totalPages = signal(1);
  totalLogs = signal(0);
  
  stats = signal<NutritionStats | null>(null);
  
  // Filtering (optional for now, but UI shows dropdown)
  daysFilter = signal<number | undefined>(undefined);
  deletingId = signal<string | null>(null);

  ngOnInit() {
    this.loadData();
    this.metabolismService.fetchSummary(3);
  }

  loadData() {
    this.isLoading.set(true);
    // ForkJoin or just separate calls? Separate is fine for now.
    this.loadLogs();
    this.loadStats();
  }

  async loadStats() {
    try {
      const s = await this.nutritionService.getStats();
      this.stats.set(s);
    } catch (error) {
    }
  }


  async loadLogs() {
    try {
      const response = await this.nutritionService.getLogs(this.currentPage(), 10, this.daysFilter());
      this.logs.set(response.logs);
      this.totalPages.set(response.total_pages);
      this.totalLogs.set(response.total);
      this.isLoading.set(false);
    } catch (err) {
      this.isLoading.set(false);
    }
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

  async deleteLog(event: Event, log: NutritionLog) {
    event.stopPropagation();
    if (confirm('Tem certeza que deseja excluir este registro nutricional?')) {
      this.deletingId.set(log.id);
      try {
        await this.nutritionService.deleteLog(log.id);
        this.currentPage.set(1);
        await this.loadData();
        this.deletingId.set(null);
      } catch (err) {
        this.deletingId.set(null);
      }
    }
  }

  // Helpers for template
  getMacroPercentage(grams: number, type: 'protein' | 'carbs' | 'fat', calories: number): string {
    if (!calories) return '0%';
    const caloriesPerGram = type === 'fat' ? 9 : 4;
    const percentage = Math.round(((grams * caloriesPerGram) / calories) * 100);
    return `${percentage}%`;
  }

}
