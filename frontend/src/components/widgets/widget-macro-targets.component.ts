import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-macro-targets',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col">
      <div class="flex justify-between items-center mb-6">
        <div>
          <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">{{ title }}</p>
          <div class="text-[10px] text-text-secondary font-bold uppercase tracking-tighter opacity-60" *ngIf="startDate && endDate">
            Período: {{ startDate | date:'dd/MM' }} a {{ endDate | date:'dd/MM' }}
          </div>
        </div>
        <div class="flex items-center gap-1" *ngIf="stabilityScore !== undefined">
           <div class="w-2 h-2 rounded-full" [ngClass]="stabilityScore > 70 ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'"></div>
           <span class="text-[10px] font-bold text-text-secondary tracking-tight">{{ stabilityScore }}% Estabilidade</span>
        </div>
      </div>

      <div class="space-y-5 flex-1 flex flex-col justify-center">
        <!-- Protein -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-end text-[10px]">
            <span class="text-white font-bold uppercase">Proteína</span>
            <span class="text-text-secondary">
              <span class="text-white font-bold">{{ avgProtein | number:'1.0-0' }}g</span>
              <span class="opacity-40 px-1">/</span>
              <span class="text-primary font-bold">{{ targetProtein | number:'1.0-0' }}g</span>
            </span>
          </div>
          <div class="h-1.5 w-full bg-secondary/20 rounded-full overflow-hidden">
            <div class="bg-primary h-full rounded-full transition-all duration-1000" [style.width.%]="getPercent(avgProtein, targetProtein)"></div>
          </div>
        </div>

        <!-- Carbs -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-end text-[10px]">
            <span class="text-white font-bold uppercase">Carbos</span>
            <span class="text-text-secondary">
               <span class="text-white font-bold">{{ avgCarbs | number:'1.0-0' }}g</span>
               <span class="opacity-40 px-1">/</span>
               <span class="text-blue-400 font-bold">{{ targetCarbs | number:'1.0-0' }}g</span>
            </span>
          </div>
          <div class="h-1.5 w-full bg-secondary/20 rounded-full overflow-hidden">
            <div class="bg-blue-400 h-full rounded-full transition-all duration-1000" [style.width.%]="getPercent(avgCarbs, targetCarbs)"></div>
          </div>
        </div>

        <!-- Fats -->
        <div class="space-y-1.5">
          <div class="flex justify-between items-end text-[10px]">
            <span class="text-white font-bold uppercase">Gorduras</span>
            <span class="text-text-secondary">
               <span class="text-white font-bold">{{ avgFat | number:'1.0-0' }}g</span>
               <span class="opacity-40 px-1">/</span>
               <span class="text-orange-400 font-bold">{{ targetFat | number:'1.0-0' }}g</span>
            </span>
          </div>
          <div class="h-1.5 w-full bg-secondary/20 rounded-full overflow-hidden">
            <div class="bg-orange-400 h-full rounded-full transition-all duration-1000" [style.width.%]="getPercent(avgFat, targetFat)"></div>
          </div>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetMacroTargetsComponent {
  @Input() title: string = 'Alvos vs Média';
  @Input() stabilityScore?: number;
  @Input() startDate?: string;
  @Input() endDate?: string;

  @Input({ required: true }) avgProtein: number = 0;
  @Input({ required: true }) targetProtein: number = 0;
  
  @Input({ required: true }) avgCarbs: number = 0;
  @Input({ required: true }) targetCarbs: number = 0;
  
  @Input({ required: true }) avgFat: number = 0;
  @Input({ required: true }) targetFat: number = 0;

  getPercent(actual: number, target: number): number {
    if (!target) return 0;
    return Math.min(100, Math.round((actual / target) * 100));
  }
}
