import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

@Component({
  selector: 'app-widget-volume-trend',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col overflow-hidden h-60">
      <div class="flex justify-between items-center mb-3">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Volume Semanal (8 semanas)</p>
        <span class="text-[8px] text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20 font-bold uppercase tracking-tighter">Kg</span>
      </div>
      <div class="flex-1 w-full min-h-0 relative">
        <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="chartType"></canvas>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetVolumeTrendComponent implements OnChanges {
  @Input() volumeTrend: number[] = [];

  public chartType: ChartType = 'line';
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
        padding: 10,
        displayColors: false
      }
    },
    scales: {
      x: {
        ticks: { color: '#a1a1aa', font: { size: 10 } },
        grid: { display: false }
      },
      y: {
        ticks: {
          color: '#a1a1aa',
          font: { size: 10 },
          callback: (value) => Math.round(Number(value))
        },
        grid: { color: 'rgba(39, 39, 42, 0.5)' },
        beginAtZero: true
      }
    }
  };

  public chartData: ChartData<'line'> = {
    labels: ['-7 sem', '-6 sem', '-5 sem', '-4 sem', '-3 sem', '-2 sem', '-1 sem', 'Atual'],
    datasets: [{
      data: [],
      label: 'Volume (kg)',
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: '#10b981'
    }]
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['volumeTrend'] && this.volumeTrend) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    this.chartData = {
      ...this.chartData,
      datasets: [{
        ...this.chartData.datasets[0],
        data: this.volumeTrend
      }]
    };
  }
}
