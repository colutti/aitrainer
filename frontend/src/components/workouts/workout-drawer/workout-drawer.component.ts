import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Workout } from '../../../models/workout.model';

@Component({
  selector: 'app-workout-drawer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './workout-drawer.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'block' }
})
export class WorkoutDrawerComponent {
  @Input({ required: true }) workout!: Workout;
  @Output() close = new EventEmitter<void>();

  get volumeTotal(): number {
    if (!this.workout?.exercises) return 0;
    return this.workout.exercises.reduce((acc, ex) => {
        const exVol = ex.weights_per_set.reduce((sAcc, w, i) => {
            const r = ex.reps_per_set[i] || 0;
            return sAcc + (w * r);
        }, 0);
        return acc + exVol;
    }, 0);
  }

  get totalSets(): number {
      return this.workout.exercises.reduce((acc, ex) => acc + ex.sets, 0);
  }
}
