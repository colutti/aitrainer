import { Component, ChangeDetectionStrategy, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkoutService } from '../../services/workout.service';
import { WorkoutDrawerComponent } from './workout-drawer/workout-drawer.component';
import { Workout } from '../../models/workout.model';
import { WorkoutStats } from '../../models/stats.model';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { WidgetStreakComponent } from '../widgets/widget-streak.component';
import { WidgetFrequencyComponent } from '../widgets/widget-frequency.component';
import { WidgetRecentPrsComponent } from '../widgets/widget-recent-prs.component';

@Component({
  selector: 'app-workouts',
  templateUrl: './workouts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'block h-full w-full' },
  standalone: true,
  imports: [CommonModule, WorkoutDrawerComponent, BaseChartDirective, WidgetStreakComponent, WidgetFrequencyComponent, WidgetRecentPrsComponent]
})
export class WorkoutsComponent implements OnInit {
  private workoutService = inject(WorkoutService);

  workouts = this.workoutService.workouts;
  isLoading = this.workoutService.isLoading;
  currentPage = this.workoutService.currentPage;
  totalPages = this.workoutService.totalPages;
  totalWorkouts = this.workoutService.totalWorkouts;
  
  selectedWorkout = signal<Workout | null>(null);
  workoutTypes = signal<string[]>([]);
  selectedType = this.workoutService.selectedType;
  deletingId = signal<string | null>(null);
  stats = signal<WorkoutStats | null>(null);

  // Volume Chart Properties
  public volumeChartType: ChartType = 'line';
  public volumeChartData: ChartData<'line'> = {
    labels: ['-7 sem', '-6 sem', '-5 sem', '-4 sem', '-3 sem', '-2 sem', '-1 sem', 'Atual'],
    datasets: [{ 
      data: [], 
      label: 'Volume (kg)', 
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: '#10b981'
    }]
  };

  public volumeChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { 
        grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
        ticks: { 
          color: '#94a3b8', 
          font: { size: 10 },
          callback: (value) => Math.round(Number(value))
        } 
      },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
    }
  };

  // Radar Chart Properties
  public radarChartType: ChartType = 'radar';
  public radarChartData: ChartData<'radar'> = {
    labels: ['Push', 'Pull', 'Legs'],
    datasets: [{ 
      data: [], 
      label: 'Strength peak ratio',
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      pointBackgroundColor: '#3b82f6'
    }]
  };

  public radarChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 11, weight: 'bold' } },
        ticks: { display: false },
        suggestedMin: 0,
        suggestedMax: 1
      }
    }
  };

  // Pull to refresh state
  private startY = 0;
  private currentY = 0;
  isPulling = signal(false);
  pullProgress = signal(0); // 0 to 100

  onTouchStart(event: TouchEvent) {
    if (window.scrollY === 0 || (event.target as HTMLElement).scrollTop === 0) {
      this.startY = event.touches[0].clientY;
      this.isPulling.set(true);
    }
  }

  onTouchMove(event: TouchEvent) {
    if (!this.isPulling()) return;
    
    this.currentY = event.touches[0].clientY;
    const diff = this.currentY - this.startY;
    
    if (diff > 0 && diff < 200) {
      // Prevent default pull-to-refresh if possible, though strict passive listeners might prevent this
      // event.preventDefault(); 
      this.pullProgress.set(Math.min((diff / 150) * 100, 100));
    }
  }

  async onTouchEnd() {
    if (!this.isPulling()) return;

    if (this.pullProgress() >= 100) {
      // Trigger refresh
      await this.loadWorkouts();
    }
    
    // Reset
    this.isPulling.set(false);
    this.pullProgress.set(0);
  }

  async loadWorkouts(): Promise<void> {
    await Promise.all([
        this.workoutService.getWorkouts(1),
        this.loadTypes(),
        this.loadStats()
    ]);
  }

  async loadStats() {
    const s = await this.workoutService.getStats();
    this.stats.set(s);
    
    if (s.volume_trend) {
       this.volumeChartData = {
         ...this.volumeChartData,
         datasets: [{ ...this.volumeChartData.datasets[0], data: s.volume_trend }]
       };
    }
    
    if (s.strength_radar) {
       const labels = Object.keys(s.strength_radar);
       const data = Object.values(s.strength_radar);
       this.radarChartData = {
         labels,
         datasets: [{ ...this.radarChartData.datasets[0], data }]
       };
    }
  }

  async ngOnInit(): Promise<void> {
    await this.loadWorkouts();
  }

  async loadTypes() {
     const types = await this.workoutService.getTypes();
     this.workoutTypes.set(types);
  }

  selectWorkout(workout: Workout) {
    this.selectedWorkout.set(workout);
  }

  closeDrawer() {
    this.selectedWorkout.set(null);
  }

  async onTypeChange(event: Event) {
      const target = event.target as HTMLSelectElement;
      const val = target.value;
      const type = val === 'all' ? null : val;
      await this.workoutService.getWorkouts(1, type);
  }

  async previousPage(): Promise<void> {
    await this.workoutService.previousPage();
  }

  async nextPage(): Promise<void> {
    await this.workoutService.nextPage();
  }

  async deleteWorkout(event: Event, workout: Workout): Promise<void> {
    event.stopPropagation();
    if (confirm('Tem certeza que deseja excluir este treino?')) {
      this.deletingId.set(workout.id);
      try {
        await this.workoutService.deleteWorkout(workout.id);
      } finally {
        this.deletingId.set(null);
      }
    }
  }

  // Helper date format for list
  formatDateMain(dateStr: string): string {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' });
  }
  
  getFormattedDate(dateStr: string): string {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('pt-BR', { 
            day: '2-digit', 
            month: 'short', 
            hour: '2-digit', 
            minute: '2-digit' 
        }).format(date);
    } catch {
        return dateStr;
    }
  } 
}
