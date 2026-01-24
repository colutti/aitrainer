import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NutritionService } from '../../services/nutrition.service';
import { NutritionLog, NutritionStats } from '../../models/nutrition.model';
import { SkeletonComponent } from '../skeleton/skeleton.component';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { WidgetMacrosTodayComponent } from '../widgets/widget-macros-today.component';
import { WidgetAdherenceComponent } from '../widgets/widget-adherence.component';

@Component({
  selector: 'app-nutrition',
  standalone: true,
  imports: [CommonModule, SkeletonComponent, BaseChartDirective, WidgetMacrosTodayComponent, WidgetAdherenceComponent],
  templateUrl: './nutrition.component.html',
})
export class NutritionComponent implements OnInit {
  private nutritionService = inject(NutritionService);

  logs = signal<NutritionLog[]>([]);
  isLoading = signal(true);
  currentPage = signal(1);
  totalPages = signal(1);
  totalLogs = signal(0);
  
  stats = signal<NutritionStats | null>(null);
  
  // Filtering (optional for now, but UI shows dropdown)
  daysFilter = signal<number | undefined>(undefined);
  deletingId = signal<string | null>(null);

  // Chart Properties
  public calorieChartType: ChartType = 'bar';
  public calorieChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{ 
      data: [], 
      label: 'Calorias',
      backgroundColor: 'rgba(16, 185, 129, 0.6)',
      borderColor: '#10b981',
      borderWidth: 1,
      borderRadius: 4,
      hoverBackgroundColor: '#10b981'
    }]
  };

  public calorieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: '#111827',
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 12 },
        padding: 10,
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { 
          color: '#94a3b8', 
          font: { size: 10 },
          callback: (value) => Math.round(Number(value))
        }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      }
    }
  };

  // --- Macros Doughnut Chart ---
  public doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: { legend: { display: false }, tooltip: { enabled: true } }
  };
  public doughnutChartType: ChartType = 'doughnut';
  public doughnutChartData: ChartData<'doughnut', number[]> = {
    labels: ['Proteína', 'Carbs', 'Gordura'],
    datasets: [{ 
       data: [0, 0, 0], 
       backgroundColor: ['#10b981', '#3b82f6', '#f97316'], 
       borderWidth: 0,
       hoverOffset: 4 
    }]
  };

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.isLoading.set(true);
    // ForkJoin or just separate calls? Separate is fine for now.
    this.loadLogs();
    this.loadStats();
  }

  loadStats() {
    this.nutritionService.getStats().subscribe({
      next: (s) => {
        this.stats.set(s);
        if (s.last_14_days) {
          this.updateCalorieChart(s.last_14_days);
        }
        if (s.today) {
           this.updateMacrosChart(s.today);
        }
      },
      error: (error) => console.error("Failed to load nutrition stats", error)
    });
  }

  updateMacrosChart(today: NutritionLog) {
      this.doughnutChartData = {
          labels: ['Proteína', 'Carbs', 'Gordura'],
          datasets: [{
              data: [today.protein_grams, today.carbs_grams, today.fat_grams] as number[],
              backgroundColor: ['#10b981', '#3b82f6', '#f97316'],
              borderWidth: 0
          }]
      };
  }

  updateCalorieChart(history: any[]) {
    const labels = history.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    });
    
    const data = history.map(d => d.calories);

    this.calorieChartData = {
      labels,
      datasets: [
        { 
          data, 
          label: 'Calorias',
          backgroundColor: history.map((d, i) => {
             // Highlight today or recent
             return i === history.length - 1 ? '#10b981' : 'rgba(16, 185, 129, 0.4)';
          }),
          borderColor: '#10b981',
          borderWidth: 1,
          borderRadius: 4,
          hoverBackgroundColor: '#10b981'
        }
      ]
    };
  }

  loadLogs() {
    // isLoading handled by loadData or kept for logs specifically? 
    // Let's keep isLoading for the main list
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

  deleteLog(event: Event, log: NutritionLog) {
    event.stopPropagation();
    if (confirm('Tem certeza que deseja excluir este registro nutricional?')) {
      this.deletingId.set(log.id);
      this.nutritionService.deleteLog(log.id).subscribe({
        next: () => {
          this.loadData();
          this.deletingId.set(null);
        },
        error: (err) => {
          console.error('Failed to delete nutrition log', err);
          this.deletingId.set(null);
        }
      });
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
    } catch {
      return dateStr;
    }
  }
}
