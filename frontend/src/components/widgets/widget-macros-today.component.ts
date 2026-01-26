import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

@Component({
  selector: 'app-widget-macros-today',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg flex flex-col items-center justify-center relative hover:border-primary/50 transition-all duration-300 h-40">
      <div *ngIf="calories > 0; else noLog" class="flex flex-col items-center justify-center w-full">
        <div class="h-24 w-24 relative">
          <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="chartType"></canvas>
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span class="text-lg font-bold text-white">{{ calories }}</span>
            <span class="text-[7px] text-text-secondary uppercase font-bold tracking-widest">kcal</span>
          </div>
        </div>
        
        <div class="flex gap-3 mt-3 w-full px-1">
            <div class="flex-1 text-center">
                <span class="text-[7px] text-[#10b981] font-black uppercase">Prot</span>
                <p class="text-[10px] font-bold text-white">{{ protein }}g</p>
            </div>
            <div class="flex-1 text-center">
                <span class="text-[7px] text-[#3b82f6] font-black uppercase">Carb</span>
                <p class="text-[10px] font-bold text-white">{{ carbs }}g</p>
            </div>
            <div class="flex-1 text-center">
                <span class="text-[7px] text-[#f97316] font-black uppercase">Gord</span>
                <p class="text-[10px] font-bold text-white">{{ fat }}g</p>
            </div>
        </div>
      </div>
      
      <ng-template #noLog>
        <div class="h-32 flex flex-col items-center justify-center opacity-40 text-center">
          <span class="text-3xl mb-2">🍎</span>
          <p class="text-xs font-bold uppercase tracking-tight">Sem logs hoje</p>
          <p class="text-[10px] mt-1">Registre sua primeira refeição!</p>
        </div>
      </ng-template>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetMacrosTodayComponent implements OnChanges {
  @Input() calories: number = 0;
  @Input() protein: number = 0;
  @Input() carbs: number = 0;
  @Input() fat: number = 0;

  public chartType: ChartType = 'doughnut';
  public chartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: { legend: { display: false }, tooltip: { enabled: true } }
  };
  
  public chartData: ChartData<'doughnut', number[]> = {
    labels: ['Proteína', 'Carbs', 'Gordura'],
    datasets: [{ 
       data: [0, 0, 0], 
       backgroundColor: ['#10b981', '#3b82f6', '#f97316'], 
       borderWidth: 0,
       hoverOffset: 4 
    }]
  };

  ngOnChanges(changes: SimpleChanges): void {
      if (changes['protein'] || changes['carbs'] || changes['fat']) {
          this.chartData = {
              labels: ['Proteína', 'Carbs', 'Gordura'],
              datasets: [{
                  data: [this.protein, this.carbs, this.fat],
                  backgroundColor: ['#10b981', '#3b82f6', '#f97316'],
                  borderWidth: 0
              }]
          };
      }
  }
}
