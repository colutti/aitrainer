import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

interface LastWorkout {
  workout_type?: string;
  date: string;
  duration_minutes?: number;
}

@Component({
  selector: 'app-widget-last-activity',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 relative overflow-hidden flex flex-col justify-center h-24">
      <div class="absolute top-0 right-0 p-3 opacity-5">
        <svg class="w-16 h-16" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
        </svg>
      </div>
      <p class="text-text-secondary text-[8px] font-bold uppercase tracking-widest mb-1.5 line-clamp-1">Última Atividade</p>
      <div *ngIf="lastWorkout; else noWorkout">
        <h3 class="text-sm font-black text-white mb-0.5 whitespace-nowrap overflow-hidden text-ellipsis">
          {{ lastWorkout.workout_type || 'Treino' }}
        </h3>
        <p class="text-[8px] text-primary font-bold uppercase tracking-tight">
          {{ getFormattedDate(lastWorkout.date) }} • {{ lastWorkout.duration_minutes || '--' }} min
        </p>
      </div>
      <ng-template #noWorkout>
        <p class="text-text-secondary italic text-[9px]">Sem treinos.</p>
      </ng-template>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetLastActivityComponent {
  @Input() lastWorkout?: LastWorkout;

  getFormattedDate(dateStr: string): string {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    return `${day}/${month}`;
  }
}
