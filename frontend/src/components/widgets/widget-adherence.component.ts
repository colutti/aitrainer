import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-adherence',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 h-24 flex flex-col justify-center">
      <div class="flex justify-between items-start mb-3">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">{{ title || 'Aderência Semanal' }}</p>
        <div class="flex items-center gap-1" *ngIf="score !== undefined">
            <span class="text-[10px] font-black text-primary">{{ score }}%</span>
        </div>
      </div>
      
      <div class="flex justify-between items-center bg-secondary/10 p-2.5 rounded-xl border border-secondary/20">
        <div *ngFor="let dayActive of weeklyAdherence; let i = index" class="flex flex-col items-center gap-1.5">
          <div [class]="dayActive ? 'bg-primary shadow-[0_0_8px_rgba(16,185,129,0.4)]' : 'bg-secondary/20'" 
               class="w-3 h-3 rounded-full transition-all duration-500"></div>
          <span class="text-[7px] font-bold text-text-secondary uppercase opacity-70">{{ ['S','T','Q','Q','S','S','D'][i] }}</span>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetAdherenceComponent {
  @Input() title?: string;
  @Input({ required: true }) weeklyAdherence: boolean[] = [];
  @Input() score?: number;
}
