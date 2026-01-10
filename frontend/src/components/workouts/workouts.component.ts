import { Component, ChangeDetectionStrategy, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkoutService } from '../../services/workout.service';
import { WorkoutDrawerComponent } from './workout-drawer/workout-drawer.component';
import { Workout } from '../../models/workout.model';

@Component({
  selector: 'app-workouts',
  templateUrl: './workouts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [CommonModule, WorkoutDrawerComponent]
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
        this.loadTypes()
    ]);
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

  // Helper date format for list
  formatDateMain(dateStr: string): string {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' });
  }
  
  // Helper for grouping? We render flat list in mockup, with Date headers.
  // Implementing date headers in HTML usually requires processing list.
  // Simplified: show date in card. Mockup: "Janeiro 2024" header.
  // We can do simple list for now (Compact List) as per Phase 3.
}
