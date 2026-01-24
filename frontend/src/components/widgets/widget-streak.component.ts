import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-streak',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex items-start justify-between group h-full">
      <div>
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider mb-1">Sequência Atual</p>
        <div class="flex items-baseline">
          <p class="text-4xl font-extrabold text-white mt-1">{{ streakWeeks }}</p>
          <span class="ml-2 text-sm font-medium text-text-secondary">semanas</span>
        </div>
      </div>
      <div class="h-10 w-10 bg-[#fb923c]/20 rounded-full flex items-center justify-center text-xl animate-pulse">
        🔥
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetStreakComponent {
  @Input({ required: true }) streakWeeks: number = 0;
}
