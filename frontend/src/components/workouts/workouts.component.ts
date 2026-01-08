import { Component, ChangeDetectionStrategy, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkoutService } from '../../services/workout.service';

@Component({
  selector: 'app-workouts',
  templateUrl: './workouts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [CommonModule]
})
export class WorkoutsComponent implements OnInit {
  private workoutService = inject(WorkoutService);

  workouts = this.workoutService.workouts;
  isLoading = this.workoutService.isLoading;
  currentPage = this.workoutService.currentPage;
  totalPages = this.workoutService.totalPages;
  totalWorkouts = this.workoutService.totalWorkouts;

  async ngOnInit(): Promise<void> {
    await this.workoutService.getWorkouts(1);
  }

  async previousPage(): Promise<void> {
    await this.workoutService.previousPage();
  }

  async nextPage(): Promise<void> {
    await this.workoutService.nextPage();
  }

  formatDate(dateStr: string): string {
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

  getWorkoutTypeGradient(type: string | null): string {
    const t = (type || '').toLowerCase();
    if (t.includes('perna') || t.includes('leg')) return 'from-blue-600 to-indigo-700';
    if (t.includes('peito') || t.includes('push')) return 'from-red-600 to-orange-700';
    if (t.includes('costas') || t.includes('pull')) return 'from-green-600 to-emerald-700';
    if (t.includes('braço') || t.includes('arm')) return 'from-purple-600 to-violet-700';
    return 'from-gray-600 to-slate-700';
  }

  getWorkoutIcon(type: string | null): string {
    const t = (type || '').toLowerCase();
    if (t.includes('perna') || t.includes('leg')) return '🦵';
    if (t.includes('peito') || t.includes('push')) return '💪';
    if (t.includes('costas') || t.includes('pull')) return '🔙';
    if (t.includes('braço') || t.includes('arm')) return '💪';
    return '🏋️';
  }

  isUniformExercise(reps: number[], weights: number[]): boolean {
    if (reps.length === 0) return true;
    const uniformReps = reps.every(r => r === reps[0]);
    const uniformWeights = weights.length === 0 || weights.every(w => w === weights[0]);
    return uniformReps && uniformWeights;
  }
}
