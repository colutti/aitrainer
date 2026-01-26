import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

interface VolumeStat {
  category: string;
  volume: number;
}

@Component({
  selector: 'app-widget-weekly-distribution',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 h-40">
      <div class="flex justify-between items-center mb-4">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Distribuição Semanal</p>
        <span class="bg-primary/10 text-primary text-[8px] px-2 py-0.5 rounded-full border border-primary/20 font-bold uppercase">Volume Kg</span>
      </div>
      <div class="h-32 w-full">
        <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="chartType"></canvas>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetWeeklyDistributionComponent implements OnChanges {
  @Input() volumeStats: VolumeStat[] = [];

  public chartType: ChartType = 'bar';
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
        ticks: { color: '#a1a1aa', font: { family: 'Inter' } },
        grid: { display: false }
      },
      y: {
        ticks: {
          color: '#a1a1aa',
          font: { family: 'Inter' },
          callback: (value) => Math.round(Number(value))
        },
        grid: { color: '#27272a' },
        beginAtZero: true
      }
    }
  };

  public chartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{ data: [], backgroundColor: '#10b981', borderRadius: 4 }]
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['volumeStats'] && this.volumeStats) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    const displayedStats = this.volumeStats.slice(0, 5);
    this.chartData = {
      labels: displayedStats.map(v => v.category),
      datasets: [{
        data: displayedStats.map(v => v.volume),
        backgroundColor: '#10b981',
        borderRadius: 4
      }]
    };
  }
}
