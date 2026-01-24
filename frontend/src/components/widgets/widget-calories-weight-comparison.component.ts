import { Component, Input, OnChanges, SimpleChanges, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

@Component({
  selector: 'app-widget-calories-weight-comparison',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-6 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors h-full flex flex-col">
      <div class="flex justify-between items-center mb-4">
        <div>
            <h3 class="text-text-secondary text-xs font-bold uppercase tracking-wider">{{ title }}</h3>
            <p class="text-xs text-text-secondary opacity-70">Correlação Diária</p>
        </div>
        <div class="flex items-center gap-3">
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-primary"></span>
                <span class="text-[10px] text-text-secondary">Peso</span>
            </div>
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                <span class="text-[10px] text-text-secondary">Calorias</span>
            </div>
        </div>
      </div>
      
      <div class="flex-1 w-full min-h-[220px]">
        <canvas baseChart
          [data]="chartData"
          [options]="chartOptions"
          [type]="'line'">
        </canvas>
      </div>
    </div>
  `
})
export class WidgetCaloriesWeightComparisonComponent implements OnChanges {
  @Input() title: string = 'Calorias vs Peso';
  @Input() weightTrend: { date: string, weight: number }[] = [];
  @Input() calorieHistory: { date: string, calories: number }[] = [];

  public chartData: ChartData<'bar' | 'line'> = {
    labels: [],
    datasets: []
  };

  public chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#18181b',
        titleColor: '#fff',
        bodyColor: '#a1a1aa',
        borderColor: '#3f3f46',
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        usePointStyle: true
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#71717a', font: { size: 10 } }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Kg', color: '#10b981', font: { size: 9 } },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#71717a', font: { size: 10 } }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: 'Kcal', color: '#3b82f6', font: { size: 9 } },
        grid: { display: false },
        ticks: { color: '#71717a', font: { size: 10 }, stepSize: 500 }
      }
    }
  };

  ngOnChanges(changes: SimpleChanges) {
    if (changes['weightTrend'] || changes['calorieHistory']) {
      this.updateChart();
    }
  }

  private updateChart() {
    if (!this.weightTrend?.length && !this.calorieHistory?.length) return;

    // Merge dates
    const weightDates = this.weightTrend.map(d => d.date.split('T')[0]);
    const calorieDates = this.calorieHistory.map(d => d.date.split('T')[0]);
    const allDates = Array.from(new Set([...weightDates, ...calorieDates])).sort();
    
    // Limit to last 14 days if too many
    const displayDates = allDates.slice(-14);

    const weights = displayDates.map(date => {
        const entry = this.weightTrend.find(d => d.date.startsWith(date));
        return entry ? entry.weight : null;
    });

    const calories = displayDates.map(date => {
        const entry = this.calorieHistory.find(d => d.date.startsWith(date));
        return entry ? entry.calories : null;
    });

    const labels = displayDates.map(d => new Date(d).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }));

    this.chartData = {
      labels,
      datasets: [
        {
          type: 'line',
          label: 'Peso (kg)',
          data: weights,
          borderColor: '#10b981',
          backgroundColor: '#10b981',
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#18181b', // hollow look
          pointBorderWidth: 2,
          tension: 0.4,
          yAxisID: 'y',
          order: 1
        },
        {
          type: 'line',
          label: 'Calorias',
          data: calories,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#3b82f6',
          tension: 0.4,
          yAxisID: 'y1',
          order: 2
        }
      ]
    };
  }
}
