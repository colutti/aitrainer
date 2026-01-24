import { Component, inject, OnInit, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { StatsService } from '../../services/stats.service';
import { NutritionService } from '../../services/nutrition.service';
import { MetabolismService } from '../../services/metabolism.service';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { VolumeStat } from '../../models/stats.model';
import { WeightLog } from '../../models/weight-log.model';
import { WeightService } from '../../services/weight.service';
import { MetabolismResponse } from '../../models/metabolism.model';
import { NutritionStats } from '../../models/nutrition.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  statsService = inject(StatsService);
  nutritionService = inject(NutritionService);
  weightService = inject(WeightService);
  metabolismService = inject(MetabolismService);
  
  stats = this.statsService.stats;
  nutritionStats = this.nutritionService.stats;
  metabolismStats = signal<MetabolismResponse | null>(null);
  latestComposition = signal<WeightLog | null>(null);
  
  isLoading = this.statsService.isLoading;
  isMetabolismLoading = signal<boolean>(false);

  // --- Volume Chart Config ---
  public barChartOptions: ChartConfiguration['options'] = {
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
        ticks: { color: '#a1a1aa', font: { family: 'Inter' } },
        grid: { color: '#27272a' },
        beginAtZero: true
      }
    }
  };
  public barChartType: ChartType = 'bar';
  public barChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [{ data: [], backgroundColor: '#10b981', borderRadius: 4 }]
  };

  // --- Calories Line Chart ---
  public lineChartOptions: ChartConfiguration['options'] = {
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
        x: { display: false },
        y: { display: false }
    },
    elements: {
        point: { radius: 2, hoverRadius: 4 },
        line: { tension: 0.4 }
    }
  };
  public lineChartType: ChartType = 'line';
  public lineChartData: ChartData<'line'> = {
      labels: [],
      datasets: [{
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          borderWidth: 2
      }]
  };

  // --- Macros Doughnut Chart ---
  public doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: { legend: { display: false }, tooltip: { enabled: true } }
  };
  public doughnutChartType: ChartType = 'doughnut';
  public doughnutChartData: ChartData<'doughnut', number[]> = {
    labels: ['Proteína', 'Carbs', 'Gordura'],
    datasets: [{ 
       data: [0, 0, 0], 
       backgroundColor: ['#10b981', '#3b82f6', '#f97316'], 
       borderWidth: 0,
       hoverOffset: 4 
    }]
  };

  // --- Weight Trend Chart ---
  public weightChartOptions: ChartConfiguration['options'] = {
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
          label: (context) => ` ${context.parsed.y.toFixed(1)} kg`
        }
      }
    },
    scales: {
      x: {
        ticks: { 
          color: '#a1a1aa', 
          font: { family: 'Inter', size: 10 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 7
        },
        grid: { display: false }
      },
      y: {
        ticks: { 
          color: '#a1a1aa', 
          font: { family: 'Inter', size: 10 },
          callback: (value) => `${value}kg`
        },
        grid: { color: 'rgba(39, 39, 42, 0.5)' },
        beginAtZero: false
      }
    },
    elements: {
        point: { radius: 3, hoverRadius: 5, backgroundColor: '#10b981', borderWidth: 0 },
        line: { tension: 0.3 }
    }
  };
  public weightChartType: ChartType = 'line';
  public weightChartData: ChartData<'line'> = {
    labels: [],
    datasets: [{
      data: [],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      borderWidth: 3,
      pointBackgroundColor: '#10b981'
    }]
  };

  // --- Consistency Chart ---
  public consistencyChartOptions: ChartConfiguration['options'] = {
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
          label: (context) => ` ${context.dataset.label}: ${context.parsed.y > 0 ? 'OK' : 'Pendente'}`
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
  public consistencyChartType: ChartType = 'bar';
  public consistencyChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [
      {
        label: 'Nutrição',
        data: [],
        backgroundColor: '#3b82f6',
        borderRadius: 2,
        stack: 'stack0'
      },
      {
        label: 'Peso',
        data: [],
        backgroundColor: '#10b981',
        borderRadius: 2,
        stack: 'stack0'
      }
    ]
  };

  constructor() {
    effect(() => {
      const s = this.stats();
      if (s?.weekly_volume) {
        this.updateVolumeChart(s.weekly_volume);
      }
    });

    effect(() => {
        const n = this.nutritionStats();
        if (n) {
            this.updateNutritionCharts(n);
        }
    });

    effect(() => {
      const m = this.metabolismStats();
      if (m) {
        if (m.weight_trend) this.updateWeightChart(m.weight_trend);
        if (m.consistency) this.updateConsistencyChart(m.consistency);
      }
    });
  }

  async ngOnInit() {
    this.statsService.fetchStats();
    this.nutritionService.getStats().subscribe();
    this.fetchMetabolismTrend();
    const compStats = await this.weightService.getBodyCompositionStats();
    if (compStats?.latest) {
        this.latestComposition.set(compStats.latest);
    }
  }

  async fetchMetabolismTrend() {
    this.isMetabolismLoading.set(true);
    try {
      const data = await this.metabolismService.getSummary(100);
      this.metabolismStats.set(data);
    } catch (e) {
      console.error('Failed to fetch dashboard metabolism trend', e);
    } finally {
      this.isMetabolismLoading.set(false);
    }
  }

  getSparklinePath(): string {
    const s = this.metabolismStats();
    const weights = s.weight_trend.map((t: { weight: number }) => t.weight);
    const min = Math.min(...weights) - 0.5;
    const max = Math.max(...weights) + 0.5;
    const range = max - min;
    
    if (range === 0) return 'M 0 20 L 100 20';
    
    const width = 100;
    const height = 40;
    
    const points = weights.map((w: number, i: number) => {
      const x = (i / (weights.length - 1)) * width;
      const y = height - ((w - min) / range) * height;
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  }

  getWeightVariation(): number {
    const s = this.metabolismStats();
    if (!s || s.start_weight === undefined || s.end_weight === undefined) return 0;
    return s.end_weight - s.start_weight;
  }

  getConsistencyStatus() {
    const s = this.metabolismStats();
    if (!s || !s.consistency) return [];
    // Show last 7 days of consistency
    return s.consistency.slice(-7);
  }

  updateConsistencyChart(consistency: { date: string, weight: boolean, nutrition: boolean }[]) {
    const last7 = consistency.slice(-7);
    this.consistencyChartData = {
      labels: last7.map(c => new Date(c.date).toLocaleDateString('pt-BR', { weekday: 'short' })),
      datasets: [
        {
          label: 'Nutrição',
          data: last7.map(c => c.nutrition ? 1 : 0),
          backgroundColor: '#3b82f6',
          borderRadius: 2,
          stack: 'stack0'
        },
        {
          label: 'Peso',
          data: last7.map(c => c.weight ? 1 : 0),
          backgroundColor: '#10b981',
          borderRadius: 2,
          stack: 'stack0'
        }
      ]
    };
  }

  updateWeightChart(trend: { date: string, weight: number, trend?: number }[]) {
    this.weightChartData = {
      labels: trend.map(t => new Date(t.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
      datasets: [
        {
          data: trend.map(t => t.weight),
          borderColor: 'rgba(16, 185, 129, 0.3)',
          backgroundColor: 'transparent',
          fill: false,
          borderWidth: 1,
          pointBackgroundColor: 'rgba(16, 185, 129, 0.6)',
          pointRadius: 2,
          label: 'Real'
        },
        {
          data: trend.map(t => t.trend ?? null),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          borderWidth: 3,
          pointRadius: 0,
          label: 'Tendência',
          tension: 0.4
        }
      ]
    };
  }

  updateVolumeChart(volumeStats: VolumeStat[]) {
    const displayedStats = volumeStats.slice(0, 5);
    this.barChartData = {
      labels: displayedStats.map(v => v.category),
      datasets: [
        {
          data: displayedStats.map(v => v.volume),
          backgroundColor: '#10b981',
          hoverBackgroundColor: '#059669',
          borderRadius: 6,
          label: 'Volume (kg)',
          barThickness: 'flex',
          maxBarThickness: 40
        }
      ]
    };
  }

  updateNutritionCharts(n: NutritionStats) {
      // 1. Macros Doughnut
      if (n.today) {
          this.doughnutChartData = {
              labels: ['Proteína', 'Carbs', 'Gordura'],
              datasets: [{
                  data: [n.today.protein_grams, n.today.carbs_grams, n.today.fat_grams] as number[],
                  backgroundColor: ['#10b981', '#3b82f6', '#f97316'],
                  borderWidth: 0
              }]
          };
      }

      // 2. Calories Line
      if (n.last_7_days) {
          this.lineChartData = {
              labels: n.last_7_days.map((d: { date: string }) => new Date(d.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
              datasets: [{
                  data: n.last_7_days.map((d: { calories: number }) => d.calories) as number[],
                  borderColor: '#10b981',
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  fill: true,
                  borderWidth: 2,
                  pointBackgroundColor: '#10b981'
              }]
          };
      }
  }

  protected readonly Array = Array;
  
  getFormattedDate(dateStr: string): string {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        // Using Intl for consistent Portuguese formatting: "09 jan., 12:17"
        // month: 'short' in pt-BR usually gives 'jan.', 'fev.', etc. or 'jan' depending on browser/implementation.
        // We will try to match the user request.
        return new Intl.DateTimeFormat('pt-BR', { 
            day: '2-digit', 
            month: 'short', 
            hour: '2-digit', 
            minute: '2-digit' 
        }).format(date);
    } catch {
        return dateStr;
    }
  } 
}
