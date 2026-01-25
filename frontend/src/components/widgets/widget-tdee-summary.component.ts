import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-tdee-summary',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col h-full relative overflow-hidden group">
      <!-- Background Ornament -->
      <div class="absolute -top-6 -right-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
      
      <div class="flex justify-between items-start mb-6">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">{{ title }}</p>
        <div class="bg-primary/10 p-2 rounded-lg text-primary">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
        </div>
      </div>

      <div class="flex gap-4 mb-6">
        <div class="flex-1">
          <p class="text-[9px] text-text-secondary uppercase font-bold tracking-tighter mb-1">Manutenção</p>
          <p class="text-xl font-black text-white whitespace-nowrap">{{ tdee | number:'1.0-0' }} <span class="text-[10px] font-medium opacity-40">KCAL</span></p>
        </div>
        <div class="w-px bg-secondary/30 h-10 self-center"></div>
        <div class="flex-1">
          <p class="text-[9px] text-primary uppercase font-bold tracking-tighter mb-1">Meta: {{ goalType || 'Ajuste' }}</p>
          <p class="text-xl font-black text-primary whitespace-nowrap">{{ targetCalories | number:'1.0-0' }} <span class="text-[10px] font-medium opacity-60">KCAL</span></p>
        </div>
      </div>

      <div class="mt-auto">
        <div class="flex justify-between items-end mb-2">
          <span class="text-[10px] text-text-secondary font-bold uppercase tracking-tighter">Balanço do Objetivo</span>
          <span class="text-xs font-bold" [ngClass]="energyBalance < 0 ? 'text-green-400' : energyBalance > 0 ? 'text-red-400' : 'text-primary'">
            {{ energyBalance > 0 ? '+' : '' }}{{ energyBalance | number:'1.0-0' }} kcal/dia
          </span>
        </div>
        <div class="h-1.5 w-full bg-secondary/20 rounded-full overflow-hidden relative">
          <!-- Neutral Line -->
          <div class="absolute inset-y-0 left-1/2 w-0.5 bg-white/20 z-10"></div>
          <!-- Progress -->
          <div class="h-full rounded-full transition-all duration-1000" 
               [ngClass]="energyBalance < 0 ? 'bg-green-400' : 'bg-red-400'"
               [style.width.%]="getBalanceWidth()"
               [style.margin-left.%]="getBalanceOffset()">
          </div>
        </div>
        <div class="flex justify-between mt-1 text-[8px] text-text-secondary uppercase font-bold tracking-tighter">
          <span>Déficit</span>
          <span>Superávit</span>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetTdeeSummaryComponent {
  @Input() title: string = 'Gasto Diário (TDEE)';
  @Input({ required: true }) tdee: number = 0;
  @Input({ required: true }) targetCalories: number = 0;
  @Input() goalType?: string;
  @Input({ required: true }) energyBalance: number = 0;

  getBalanceWidth(): number {
    const abs = Math.abs(this.energyBalance);
    return Math.min(50, (abs / 1000) * 100);
  }

  getBalanceOffset(): number {
    if (this.energyBalance >= 0) return 50;
    return 50 - this.getBalanceWidth();
  }
}
