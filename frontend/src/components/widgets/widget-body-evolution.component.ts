import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-body-evolution',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex items-start justify-between group min-h-[90px] h-full">
      <div class="flex-1">
        <div class="flex justify-between items-center mb-2">
          <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Evolução Composição</p>
          <div *ngIf="fatChange < 0 && muscleChange > 0" 
               class="text-[9px] text-yellow-400 bg-yellow-400/10 px-1.5 py-0.25 rounded border border-yellow-400/20 font-bold uppercase animate-pulse">
            Recomposição 🔥
          </div>
        </div>
        
        <div class="text-[9px] text-text-secondary font-bold uppercase tracking-tight opacity-50 mb-3" *ngIf="startDate && endDate">
          {{ startDate | date:'dd/MM' }} - {{ endDate | date:'dd/MM' }}
        </div>
        
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-secondary/10 p-2 rounded-xl border border-secondary/20">
            <p class="text-[9px] text-text-secondary uppercase font-bold mb-0.5">Gordura</p>
            <span class="text-lg font-bold" [ngClass]="fatChange < 0 ? 'text-green-400' : 'text-red-400'">
              {{ fatChange > 0 ? '+' : '' }}{{ fatChange | number:'1.1-1' }}<span class="text-[10px] font-normal ml-0.5">kg</span>
            </span>
          </div>
          <div class="bg-secondary/10 p-2 rounded-xl border border-secondary/20">
            <p class="text-[9px] text-text-secondary uppercase font-bold mb-0.5">Músculo</p>
            <span class="text-lg font-bold text-primary">
              {{ muscleChange > 0 ? '+' : '' }}{{ muscleChange | number:'1.1-1' }}<span class="text-[10px] font-normal ml-0.5">kg</span>
            </span>
          </div>
        </div>
      </div>
      <span class="text-3xl ml-4 opacity-10 group-hover:opacity-40 transition-opacity">💪</span>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetBodyEvolutionComponent {
  @Input({ required: true }) fatChange: number = 0;
  @Input({ required: true }) muscleChange: number = 0;
  @Input() startDate?: string;
  @Input() endDate?: string;
}
