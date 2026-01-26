import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-calorie-volatility',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg flex flex-col justify-center items-center text-center relative overflow-hidden group h-24">
      <div class="absolute -top-10 -right-10 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
      <p class="text-text-secondary text-[9px] font-bold uppercase tracking-wider mb-1">Consistência Alimentar</p>
      <div class="flex items-center gap-3">
        <span class="text-xl">⚖️</span>
        <div class="text-left">
          <p class="text-xs font-black text-white">{{ getStabilityLabel() }}</p>
          <p class="text-[8px] text-text-secondary uppercase tracking-tighter">
            Variância <span class="text-primary font-bold">±{{ variance }}kcal</span>
          </p>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetCalorieVolatilityComponent {
  @Input() variance: number = 0;

  getStabilityLabel(): string {
    if (this.variance < 100) return 'Muito Estável';
    if (this.variance < 200) return 'Estável';
    if (this.variance < 300) return 'Moderado';
    return 'Variável';
  }
}
