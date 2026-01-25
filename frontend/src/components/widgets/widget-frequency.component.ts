import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-frequency',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 min-h-[90px] flex flex-col justify-center">
      <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider mb-3">{{ title || 'Frequência Semanal' }}</p>
      <div class="flex justify-between items-center px-1">
        <div *ngFor="let dayActive of weeklyFrequency; let i = index" class="flex flex-col items-center gap-1.5">
          <div [class]="dayActive ? 'bg-primary shadow-[0_0_8px_rgba(16,185,129,0.5)] scale-105' : 'bg-secondary/20'" 
               class="w-3.5 h-3.5 rounded-full transition-all duration-300"></div>
          <span class="text-[8px] font-bold text-text-secondary uppercase">{{ ['S','T','Q','Q','S','S','D'][i] }}</span>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetFrequencyComponent {
  @Input() title?: string;
  @Input({ required: true }) weeklyFrequency: boolean[] = [];
}
