import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

interface StrengthRadar {
  push: number;
  pull: number;
  legs: number;
}

@Component({
  selector: 'app-widget-strength-radar',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg flex flex-col relative overflow-hidden group h-60">
      <div class="absolute inset-0 bg-blue-500/5 pointer-events-none group-hover:bg-blue-500/10 transition-colors"></div>
      <div class="flex justify-between items-center mb-3 relative z-10">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Equilíbrio de Força</p>
        <span class="text-[8px] text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded border border-blue-400/20 font-bold uppercase tracking-tighter">Radar</span>
      </div>
      <div class="flex-1 w-full min-h-0 relative z-10 flex items-center justify-center">
        <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="chartType"></canvas>
      </div>
      <p class="text-[8px] text-text-secondary mt-1 italic text-center opacity-60 relative z-10">Atual vs. Máximo Histórico</p>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetStrengthRadarComponent implements OnChanges {
  @Input() strengthRadar: StrengthRadar = { push: 0, pull: 0, legs: 0 };

  public chartType: ChartType = 'radar';
  public chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#18181b',
        titleColor: '#fff',
        bodyColor: '#a1a1aa',
        borderColor: '#3f3f46',
        borderWidth: 1,
        padding: 10
      }
    },
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 10, weight: 'bold' } },
        ticks: { display: false },
        suggestedMin: 0,
        suggestedMax: 1
      }
    }
  };

  public chartData: ChartData<'radar'> = {
    labels: ['Push', 'Pull', 'Legs'],
    datasets: [{
      data: [],
      label: 'Strength peak ratio',
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      pointBackgroundColor: '#3b82f6'
    }]
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['strengthRadar'] && this.strengthRadar) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    this.chartData = {
      ...this.chartData,
      datasets: [{
        ...this.chartData.datasets[0],
        data: Object.values(this.strengthRadar)
      }]
    };
  }
}
