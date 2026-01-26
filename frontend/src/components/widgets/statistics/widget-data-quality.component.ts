import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-data-quality',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col justify-center text-center group h-40">
      <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/0 via-primary/40 to-primary/0 scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
      <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider mb-2">Confiança nos Dados</p>
      <div class="flex items-center justify-center gap-4">
        <span class="text-4xl font-black text-primary">{{ consistencyScore }}%</span>
        <div class="text-left">
          <p class="text-[10px] text-text-secondary uppercase font-bold">Nível de Confiança</p>
          <p class="text-[10px] text-white font-medium opacity-60">Baseado em {{ weightLogsCount }} pesagens</p>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetDataQualityComponent {
  @Input() consistencyScore: number = 0;
  @Input() weightLogsCount: number = 0;
}
