import { Component, ChangeDetectionStrategy, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkoutService } from '../../services/workout.service';
import { WorkoutDrawerComponent } from './workout-drawer/workout-drawer.component';
import { Workout } from '../../models/workout.model';
import { WorkoutStats } from '../../models/stats.model';
import { AppDateFormatPipe } from '../../pipes/date-format.pipe';
import { WidgetStreakComponent } from '../widgets/widget-streak.component';
import { WidgetFrequencyComponent } from '../widgets/widget-frequency.component';
import { WidgetRecentPrsComponent } from '../widgets/widget-recent-prs.component';
import { WidgetVolumeTrendComponent } from '../widgets/workouts/widget-volume-trend.component';
import { WidgetStrengthRadarComponent } from '../widgets/workouts/widget-strength-radar.component';

@Component({
  selector: 'app-workouts',
  templateUrl: './workouts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'block h-full w-full' },
  standalone: true,
  imports: [CommonModule, AppDateFormatPipe, WorkoutDrawerComponent, WidgetStreakComponent, WidgetFrequencyComponent, WidgetRecentPrsComponent, WidgetVolumeTrendComponent, WidgetStrengthRadarComponent]
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
