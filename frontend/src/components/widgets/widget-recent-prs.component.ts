import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PersonalRecord } from '../../models/stats.model';

@Component({
  selector: 'app-widget-recent-prs',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg overflow-hidden flex flex-col hover:border-primary/50 transition-colors duration-300 min-h-[90px]">
      <div class="flex justify-between items-center mb-3">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Recordes Recentes</p>
        <span class="text-sm">🏆</span>
      </div>
      
      <div *ngIf="prs.length > 0; else noPrs" class="space-y-2 overflow-y-auto max-h-40 pr-2 custom-scrollbar flex-1">
        <div *ngFor="let pr of prs" class="flex items-center justify-between p-2 rounded-xl bg-secondary/10 hover:bg-secondary/30 transition-colors border border-transparent hover:border-secondary/50 group">
          <div>
            <p class="font-bold text-white text-xs group-hover:text-primary transition-colors truncate max-w-[100px]">{{ pr.exercise_name }}</p>
            <p class="text-[8px] text-text-secondary uppercase mt-0.5 tracking-tight">{{ getFormattedDate(pr.date) }}</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-bold text-primary">{{ pr.weight }}<span class="text-[10px] ml-0.5 font-normal text-primary/70">kg</span></p>
          </div>
        </div>
      </div>
      
      <ng-template #noPrs>
        <div class="flex-1 flex flex-col items-center justify-center text-center opacity-[60%] py-4">
          <span class="text-xl mb-1 grayscale">🏅</span>
          <p class="text-text-secondary text-[10px]">Sem recordes.</p>
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
