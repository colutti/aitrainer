import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-confidence',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg rounded-2xl border border-secondary p-4 flex flex-col justify-between shadow-lg hover:border-primary/50 transition-colors h-full">
      <div class="flex justify-between items-center mb-2">
        <h3 class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Confiança</h3>
        <div class="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border"
             [ngClass]="getConfidenceColor(confidence)">
          {{ confidence || "N/A" }}
        </div>
      </div>
      
      <div class="flex flex-col items-center justify-center flex-1 py-1">
        <div class="relative w-24 h-12 overflow-hidden mb-1">
          <div class="absolute w-24 h-24 rounded-full border-[8px] border-secondary/30 border-t-2 border-l-2 -rotate-45"></div>
          <div class="absolute w-24 h-24 rounded-full border-[8px] border-transparent border-t-[var(--color-gauge)] border-r-[var(--color-gauge)] -rotate-45 transition-all duration-1000"
               [style.--color-gauge]="getConfidenceColorHex(confidence)"
               [style.clip-path]="getClipPath(confidence)">
          </div>
        </div>
      </div>
      
      <p class="text-[9px] text-text-secondary leading-tight text-center">{{ reason }}</p>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetConfidenceComponent {
  @Input() confidence: 'high' | 'medium' | 'low' | 'none' = 'none';
  @Input() reason: string = '';

  getConfidenceColor(level: string): string {
    switch(level) {
        case 'high': return 'text-green-400 border-green-400/20 bg-green-400/5';
        case 'medium': return 'text-yellow-400 border-yellow-400/20 bg-yellow-400/5';
        case 'low': return 'text-red-400 border-red-400/20 bg-red-400/5';
        default: return 'text-gray-400 border-gray-400/20 bg-gray-400/5';
    }
  }

  getConfidenceColorHex(level: string | undefined): string {
      switch(level) {
          case 'high': return '#4ade80';
          case 'medium': return '#facc15';
          case 'low': return '#f87171';
          default: return '#9ca3af';
      }
  }

  getClipPath(level: string): string {
      if (level === 'high') return 'inset(0 0 50% 0)';
      if (level === 'medium') return 'inset(0 25% 50% 0)';
      return 'inset(0 70% 50% 0)';
  }
}
