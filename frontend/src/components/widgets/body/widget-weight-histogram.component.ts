import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

interface ConsistencyData {
  date: string;
  weight: boolean;
  nutrition: boolean;
}

@Component({
  selector: 'app-widget-weight-histogram',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 h-60">
      <div class="flex justify-between items-center mb-4">
        <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">Consistência de Registros ({{ consistency.length }} dias)</p>
        <div class="flex gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-[#10b981]"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-[#3b82f6]"></span>
        </div>
      </div>
      <div class="h-48 w-full">
        <canvas baseChart [data]="chartData" [options]="chartOptions" [type]="chartType"></canvas>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetWeightHistogramComponent implements OnChanges {
  @Input() consistency: ConsistencyData[] = [];

  public chartType: ChartType = 'bar';
  public chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: { color: '#a1a1aa', boxWidth: 10, font: { size: 10, family: 'Inter' } }
      },
      tooltip: {
        backgroundColor: '#18181b',
        titleColor: '#fff',
        bodyColor: '#a1a1aa',
        borderColor: '#3f3f46',
        borderWidth: 1,
        padding: 8,
        callbacks: {
          label: (context) => {
            const status = context.parsed.y > 0 ? 'Registrado ✅' : 'Pendente ❌';
            return ` ${context.dataset.label}: ${status}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#a1a1aa', font: { family: 'Inter', size: 9 } },
        grid: { display: false }
      },
      y: {
        max: 2,
        ticks: { display: false },
        grid: { display: false }
      }
    }
  };

  public chartData: ChartData<'bar'> = {
    labels: [],
    datasets: [
      {
        label: 'Nutrição',
        data: [],
        backgroundColor: '#10b981',
        borderRadius: 4,
        barThickness: 8
      },
      {
        label: 'Peso',
        data: [],
        backgroundColor: '#3b82f6',
        borderRadius: 4,
        barThickness: 8
      }
    ]
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['consistency'] && this.consistency) {
      this.updateChart();
    }
  }

  private updateChart(): void {
    const data = this.consistency;
    this.chartData = {
      labels: data.map(c => new Date(c.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
      datasets: [
        {
          label: 'Nutrição',
          data: data.map(c => c.nutrition ? 1 : 0),
          backgroundColor: '#10b981',
          borderRadius: 4,
          barThickness: 'flex',
          maxBarThickness: 12
        },
        {
          label: 'Peso',
          data: data.map(c => c.weight ? 1 : 0),
          backgroundColor: '#3b82f6',
          borderRadius: 4,
          barThickness: 'flex',
          maxBarThickness: 12
        }
      ]
    };
  }
}
