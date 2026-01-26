import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';

interface CalorieDay {
  date: string;
  calories: number;
}

@Component({
  selector: 'app-widget-calorie-history',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors flex flex-col h-60">
      <div class="flex justify-between items-center mb-4">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Histórico de Calorias (14 dias)</p>
        <span class="text-[8px] text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20 font-bold uppercase tracking-tighter">Kcal / Dia</span>
      </div>
      <div class="flex-1 w-full min-h-0 relative">
        <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="'bar'"></canvas>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetCalorieHistoryComponent implements OnChanges {
  @Input() calorieHistory: CalorieDay[] = [];

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
        displayColors: false,
        callbacks: {
          label: (context) => ` ${context.parsed.y} kcal`
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#a1a1aa', font: { size: 9 } },
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

  public chartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: '#10b981',
      borderRadius: 4,
      barThickness: 12
    }]
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['calorieHistory'] && this.calorieHistory) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    this.chartData = {
      labels: this.calorieHistory.map(d => new Date(d.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
      datasets: [{
        data: this.calorieHistory.map(d => d.calories),
        backgroundColor: '#10b981',
        borderRadius: 4,
        barThickness: 12
      }]
    };
  }
}
