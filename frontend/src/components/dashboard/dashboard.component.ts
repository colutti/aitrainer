import { Component, inject, OnInit, signal, effect, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { TrainerCard } from '../../models/trainer-profile.model';
import { StatsService } from '../../services/stats.service';
import { NutritionService } from '../../services/nutrition.service';
import { MetabolismService } from '../../services/metabolism.service';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { VolumeStat } from '../../models/stats.model';
import { WeightLog } from '../../models/weight-log.model';
import { WeightService } from '../../services/weight.service';
import { MetabolismResponse } from '../../models/metabolism.model';
import { NutritionStats } from '../../models/nutrition.model';
import { WidgetStreakComponent } from '../widgets/widget-streak.component';
import { WidgetFrequencyComponent } from '../widgets/widget-frequency.component';
import { WidgetRecentPrsComponent } from '../widgets/widget-recent-prs.component';
import { WidgetMacrosTodayComponent } from '../widgets/widget-macros-today.component';
import { WidgetAdherenceComponent } from '../widgets/widget-adherence.component';
import { WidgetMetabolicGaugeComponent } from '../widgets/widget-metabolic-gauge.component';
import { WidgetBodyEvolutionComponent } from '../widgets/widget-body-evolution.component';
import { WidgetLineChartComponent } from '../widgets/widget-line-chart.component';
import { WidgetCaloriesWeightComparisonComponent } from '../widgets/widget-calories-weight-comparison.component';
import { WidgetMacroTargetsComponent } from '../widgets/widget-macro-targets.component';
import { WidgetTdeeSummaryComponent } from '../widgets/widget-tdee-summary.component';
import { SectionHeaderComponent } from '../widgets/shared/section-header.component';
import { WidgetLastActivityComponent } from '../widgets/workouts/widget-last-activity.component';
import { WidgetWeeklyDistributionComponent } from '../widgets/workouts/widget-weekly-distribution.component';
import { WidgetStrengthRadarComponent } from '../widgets/workouts/widget-strength-radar.component';
import { WidgetCalorieVolatilityComponent } from '../widgets/nutrition/widget-calorie-volatility.component';
import { WidgetWeightHistogramComponent } from '../widgets/body/widget-weight-histogram.component';
import { WidgetDataQualityComponent } from '../widgets/statistics/widget-data-quality.component';
import { WidgetAverageCaloriesComponent } from '../widgets/nutrition/widget-average-calories.component';
import { AppNumberFormatPipe } from '../../pipes/number-format.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    AppNumberFormatPipe,
    WidgetStreakComponent,
    WidgetFrequencyComponent,
    WidgetRecentPrsComponent,
    WidgetMacrosTodayComponent,
    WidgetAdherenceComponent,
    WidgetMetabolicGaugeComponent,
    WidgetBodyEvolutionComponent,
    WidgetLineChartComponent,
    WidgetCaloriesWeightComparisonComponent,
    WidgetMacroTargetsComponent,
    WidgetTdeeSummaryComponent,
    SectionHeaderComponent,
    WidgetLastActivityComponent,
    WidgetWeeklyDistributionComponent,
    WidgetStrengthRadarComponent,
    WidgetCalorieVolatilityComponent,
    WidgetWeightHistogramComponent,
    WidgetDataQualityComponent,
    WidgetAverageCaloriesComponent
  ],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  statsService = inject(StatsService);
  nutritionService = inject(NutritionService);
  weightService = inject(WeightService);
  metabolismService = inject(MetabolismService);
  trainerService = inject(TrainerProfileService);
  
  stats = this.statsService.stats;
  nutritionStats = this.nutritionService.stats;
  metabolismStats = signal<MetabolismResponse | null>(null);
  latestComposition = signal<WeightLog | null>(null);
  
  isLoading = this.statsService.isLoading;
  isMetabolismLoading = signal<boolean>(false);
  
  currentTrainer = signal<TrainerCard | null>(null);

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
        y: { 
            display: false,
            ticks: { callback: (value) => Math.round(Number(value)) }
        }
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
          borderWidth: 2,
          pointRadius: 2,
          label: 'Calorias'
      }]
  };

  // --- Volume Trend Chart (8 weeks) ---
  public volumeTrendChartData: ChartData<'line'> = {
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

  // --- Strength Radar Chart ---
  public radarChartData: ChartData<'radar'> = {
    labels: ['Push', 'Pull', 'Legs'],
    datasets: [{ 
      data: [], 
      label: 'Strength peak ratio',
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      pointBackgroundColor: '#3b82f6'
    }]
  };

  public radarChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
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

  public volumeTrendChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { 
        grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
        ticks: { color: '#94a3b8', font: { size: 10 }, callback: (v) => Math.round(Number(v)) } 
      },
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
    }
  };

  // --- Fat & Muscle Trends ---
  public fatTrendChartData: ChartData<'line'> = {
    labels: [],
    datasets: [{
        data: [],
        borderColor: '#f97316',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        fill: true,
        pointRadius: 3,
        label: 'Gordura (%)',
        spanGaps: true
    }]
  };

  public muscleTrendChartData: ChartData<'line'> = {
    labels: [],
    datasets: [{
        data: [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        pointRadius: 3,
        label: 'Músculo (%)',
        spanGaps: true
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

  public compositionChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        backgroundColor: '#18181b',
        titleColor: '#fff',
        bodyColor: '#a1a1aa',
        borderColor: '#3f3f46',
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
        }
      },
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          color: '#a1a1aa',
          boxWidth: 8,
          usePointStyle: true,
          pointStyle: 'circle',
          font: { size: 9 }
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
          callback: (value) => `${Number(value).toFixed(1)}%`
        },
        grid: { color: 'rgba(39, 39, 42, 0.5)' },
        beginAtZero: false
      }
    },
    elements: {
        point: { radius: 3, hoverRadius: 5, backgroundColor: '#3b82f6', borderWidth: 0 },
        line: { tension: 0.3 }
    }
  };

  // --- Weight Trend Chart ---
  public weightChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        backgroundColor: '#18181b',
        titleColor: '#fff',
        bodyColor: '#a1a1aa',
        borderColor: '#3f3f46',
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toFixed(1)} kg`
        }
      },
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          color: '#a1a1aa',
          boxWidth: 8,
          usePointStyle: true,
          pointStyle: 'circle',
          font: { size: 9 }
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
          callback: (value) => `${Number(value).toFixed(1)}kg`
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
      if (s) {
        if (s.weekly_volume) this.updateVolumeChart(s.weekly_volume);
        if (s.volume_trend) {
           this.volumeTrendChartData = {
              ...this.volumeTrendChartData,
              datasets: [{ ...this.volumeTrendChartData.datasets[0], data: s.volume_trend }]
           };
        }
        if (s.strength_radar) {
           this.radarChartData = {
              labels: Object.keys(s.strength_radar),
              datasets: [{ ...this.radarChartData.datasets[0], data: Object.values(s.strength_radar) }]
           };
        }
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

    effect(async () => {
       const comp = await this.weightService.getBodyCompositionStats();
       if (comp) {
          const allDates = comp.weight_trend || [];
          const labels = allDates.map(d => new Date(d.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }));
          
          // Align data points with labels to prevent shifting
          const fatData = allDates.map(d => {
             const entry = comp.fat_trend?.find(f => f.date === d.date);
             return entry ? entry.value : null;
          });

          const muscleData = allDates.map(d => {
             const entry = comp.muscle_trend?.find(m => m.date === d.date);
             return entry ? entry.value : null;
          });

          this.fatTrendChartData = {
            labels,
            datasets: [{ ...this.fatTrendChartData.datasets[0], data: fatData }]
          };
          
          this.muscleTrendChartData = {
            labels,
            datasets: [{ ...this.muscleTrendChartData.datasets[0], data: muscleData }]
          };
       }
    });


    
    // Auto-load trainer on init (simulated by empty dependency effect or explicit call in OnInit, but we want reactivity to profile change if possible)
    // Actually we can just load it once.
    effect(async () => {
        // We need user profile access? Not necessarily, trainer service handles its own state usually.
        // But let's follow the pattern from MetabolismComponent which uses userProfileService.userProfile.
        // Since we don't have profile signal here yet, let's just fetch directly.
        try {
            const trainers = await this.trainerService.getAvailableTrainers();
            const trainerProfile = await this.trainerService.fetchProfile();
            const matched = trainers.find(t => t.trainer_id === trainerProfile.trainer_type);
            
            if (matched) {
                this.currentTrainer.set(matched);
            }
        } catch (e) {
            console.error('Failed to load trainer for dashboard', e);
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

  getMetabolicBalanceProgress(): number {
    const s = this.metabolismStats();
    if (!s || !s.energy_balance) return 50; // Center
    
    // Scale -500 to +500 into 0 to 100
    const balance = s.energy_balance;
    const progress = ((balance + 500) / 1000) * 100;
    return Math.min(100, Math.max(0, progress));
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

      // 2. Calories Line (14 days)
      if (n.last_14_days) {
          this.lineChartData = {
              labels: n.last_14_days.map((d: { date: string }) => new Date(d.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
              datasets: [{
                  data: n.last_14_days.map((d: { calories: number }) => d.calories) as number[],
                  borderColor: '#10b981',
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  fill: true,
                  borderWidth: 2,
                  pointBackgroundColor: '#10b981',
                  pointRadius: 2,
                  label: 'Calorias'
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

