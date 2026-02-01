import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-consistency-score',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg rounded-2xl border border-secondary p-4 flex flex-col justify-center items-center shadow-lg hover:border-primary/50 transition-colors h-full">
      <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider mb-2 w-full text-left">
        Consistência
      </p>
      <div class="text-3xl font-black text-primary">
        {{ score }}%
      </div>
      <p class="text-[9px] text-text-secondary uppercase font-bold mt-1">
        Dados Confiáveis
      </p>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetConsistencyScoreComponent {
  @Input() score: number = 0;
}
