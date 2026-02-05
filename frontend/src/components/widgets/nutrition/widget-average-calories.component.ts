import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-average-calories',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col h-full relative overflow-hidden group">
      <!-- Background Ornament -->
      <div class="absolute -top-6 -right-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
      
      <div class="flex justify-between items-start mb-6">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Médias de Consumo</p>
        <div class="bg-primary/10 p-2 rounded-lg text-primary">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
        </div>
      </div>

      <div class="flex gap-4 mb-2">
        <div class="flex-1">
          <p class="text-[9px] text-text-secondary uppercase font-bold tracking-tighter mb-1">Últimos 7 dias</p>
          <p class="text-xl font-black text-white whitespace-nowrap" data-test="avg-7-days">{{ avg7Days | number:'1.0-0' }} <span class="text-[10px] font-medium opacity-40">KCAL</span></p>
        </div>
        <div class="w-px bg-secondary/30 h-10 self-center"></div>
        <div class="flex-1">
          <p class="text-[9px] text-text-secondary uppercase font-bold tracking-tighter mb-1">Últimos 14 dias</p>
          <p class="text-xl font-black text-white whitespace-nowrap" data-test="avg-14-days">{{ avg14Days | number:'1.0-0' }} <span class="text-[10px] font-medium opacity-40">KCAL</span></p>
        </div>
      </div>
      
      <div class="mt-auto pt-2 border-t border-secondary/20">
        <p class="text-[8px] text-text-secondary/60">Calculado com base no histórico de registros.</p>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetAverageCaloriesComponent {
  @Input({ required: true }) avg7Days: number = 0;
  @Input({ required: true }) avg14Days: number = 0;
}
