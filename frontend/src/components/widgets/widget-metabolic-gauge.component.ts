import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-widget-metabolic-gauge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 flex flex-col justify-between min-h-[90px] h-full">
      <div class="flex justify-between items-start mb-3">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Fase Metabólica</p>
        <span class="text-[9px] font-bold uppercase px-2 py-0.5 rounded border" [ngClass]="{
            'text-red-400 border-red-400/20 bg-red-400/5': status === 'surplus',
            'text-blue-400 border-blue-400/20 bg-blue-400/5': status === 'deficit',
            'text-primary border-primary/20 bg-primary/5': status === 'maintenance'
        }">{{ status === 'surplus' ? 'Superávit' : (status === 'deficit' ? 'Déficit' : 'Manutenção') }}</span>
      </div>
      
      <div class="flex-1 flex flex-col justify-center">
        <div class="relative h-2.5 w-full bg-secondary/20 rounded-full overflow-hidden mb-2">
          <div class="absolute inset-y-0 left-1/2 w-0.5 bg-white/20 z-10" title="Manutenção"></div>
          <div class="h-full rounded-full transition-all duration-1000" 
               [style.width.%]="progress"
               [ngClass]="{
                   'bg-blue-400': energyBalance < -150,
                   'bg-primary': energyBalance >= -150 && energyBalance <= 150,
                   'bg-red-400': energyBalance > 150
               }">
          </div>
        </div>
        <div class="flex justify-between items-center text-[8px] text-text-secondary font-bold uppercase tracking-tighter">
          <span>← Déficit</span>
          <span class="text-white text-xs font-black">{{ energyBalance | number:'1.0-0' }} <span class="text-[8px] font-normal opacity-60">kcal/dia</span></span>
          <span>Superávit →</span>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetMetabolicGaugeComponent {
  @Input({ required: true }) status: 'surplus' | 'deficit' | 'maintenance' = 'maintenance';
  @Input({ required: true }) energyBalance: number = 0;
  
  get progress(): number {
      // Scale -500 to +500 into 0 to 100
      const prog = ((this.energyBalance + 500) / 1000) * 100;
      return Math.min(100, Math.max(0, prog));
  }
}
