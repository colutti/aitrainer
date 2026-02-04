import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface WeeklyGoal {
  label: string;
  current: number;
  target: number;
  unit?: string;
  color?: string;
}

@Component({
  selector: 'app-widget-weekly-goals',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg border border-secondary rounded-lg p-6 h-40 shadow-lg">
      <h3 class="text-lg font-semibold text-text-primary mb-4">Metas da Semana</h3>

      <div class="space-y-3">
        @for (goal of goals; track goal.label) {
          <div class="flex items-center gap-3">
            <!-- Label -->
            <div class="min-w-20 text-sm font-medium text-text-secondary">
              {{ goal.label }}
            </div>

            <!-- Progress Bar -->
            <div class="flex-1">
              <div class="bg-dark-bg rounded-full h-2 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  [ngClass]="getProgressColor(goal)"
                  [style.width.%]="getProgressPercent(goal)">
                </div>
              </div>
            </div>

            <!-- Value -->
            <div class="min-w-20 text-right text-sm font-semibold text-text-primary">
              {{ goal.current }}{{ goal.unit || '' }} / {{ goal.target }}{{ goal.unit || '' }}
            </div>
          </div>
        }
      </div>
    </div>
  `,
})
export class WidgetWeeklyGoalsComponent {
  @Input() goals: WeeklyGoal[] = [];

  getProgressPercent(goal: WeeklyGoal): number {
    const percent = (goal.current / goal.target) * 100;
    return Math.min(percent, 100);
  }

  getProgressColor(goal: WeeklyGoal): string {
    const percent = this.getProgressPercent(goal);

    if (percent >= 100) return 'bg-success';
    if (percent >= 75) return 'bg-primary';
    if (percent >= 50) return 'bg-accent';
    return 'bg-secondary';
  }
}
