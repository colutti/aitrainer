import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PersonalRecord } from '../../models/stats.model';

@Component({
  selector: 'app-widget-recent-prs',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-6 rounded-2xl border border-secondary shadow-lg overflow-hidden flex flex-col hover:border-primary/50 transition-colors duration-300 h-full">
      <div class="flex justify-between items-center mb-4">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Recordes Recentes</p>
        <span class="text-lg">🏆</span>
      </div>
      
      <div *ngIf="prs.length > 0; else noPrs" class="space-y-3 overflow-y-auto max-h-64 pr-2 custom-scrollbar flex-1">
        <div *ngFor="let pr of prs" class="flex items-center justify-between p-3 rounded-xl bg-secondary/10 hover:bg-secondary/30 transition-colors border border-transparent hover:border-secondary/50 group">
          <div>
            <p class="font-bold text-white text-sm group-hover:text-primary transition-colors truncate max-w-[120px]">{{ pr.exercise_name }}</p>
            <p class="text-[9px] text-text-secondary uppercase mt-0.5 tracking-wide">{{ getFormattedDate(pr.date) }}</p>
          </div>
          <div class="text-right">
            <p class="text-base font-bold text-primary">{{ pr.weight }}<span class="text-xs ml-0.5 font-normal text-primary/70">kg</span></p>
            <div class="flex items-center justify-end text-[9px] text-text-secondary space-x-1">
              <span>{{ pr.reps }} reps</span>
            </div>
          </div>
        </div>
      </div>
      
      <ng-template #noPrs>
        <div class="flex-1 flex flex-col items-center justify-center text-center opacity-60">
          <span class="text-3xl mb-2 grayscale">🏅</span>
          <p class="text-text-secondary text-xs">Sem novos recordes ainda.</p>
          <p class="text-text-secondary text-[10px] mt-1">Continue firme!</p>
        </div>
      </ng-template>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetRecentPrsComponent {
  @Input({ required: true }) prs: PersonalRecord[] = [];

  getFormattedDate(dateStr: string): string {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' }).format(date);
    } catch {
      return dateStr;
    }
  }
}
