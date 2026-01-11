import { Component, inject, OnInit, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { StatsService } from '../../services/stats.service';
import { NutritionService } from '../../services/nutrition.service';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { VolumeStat } from '../../models/stats.model';

import { WeightWidgetComponent } from './weight-widget/weight-widget.component';
import { WeightService } from '../../services/weight.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, WeightWidgetComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  statsService = inject(StatsService);
  nutritionService = inject(NutritionService);
  weightService = inject(WeightService);
  
  stats = this.statsService.stats;
  nutritionStats = this.nutritionService.stats;
  latestComposition = signal<any>(null);
  
  isLoading = this.statsService.isLoading;

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

  // --- Macros Doughnut Chart ---
  public doughnutChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: { legend: { display: false }, tooltip: { enabled: true } }
  } as any; // Cast to any to allow 'cutout' which is valid for Doughnut but strict typing might miss it in generic Options
  public doughnutChartType: ChartType = 'doughnut';
  public doughnutChartData: ChartData<'doughnut'> = {
    labels: ['Proteína', 'Carbs', 'Gordura'],
    datasets: [{ 
       data: [0, 0, 0], 
       backgroundColor: ['#10b981', '#3b82f6', '#f97316'], 
       borderWidth: 0,
       hoverOffset: 4 
    }]
  };

  // --- Calories Line Chart ---
  public lineChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
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
  }

  async ngOnInit() {
    this.statsService.fetchStats();
    this.nutritionService.getStats().subscribe();
    const compStats = await this.weightService.getBodyCompositionStats();
    if (compStats?.latest) {
        this.latestComposition.set(compStats.latest);
    }
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

  updateNutritionCharts(n: any) {
      // 1. Macros Doughnut
      if (n.today) {
          this.doughnutChartData = {
              labels: ['Proteína', 'Carbs', 'Gordura'],
              datasets: [{
                  data: [n.today.protein_grams, n.today.carbs_grams, n.today.fat_grams],
                  backgroundColor: ['#10b981', '#3b82f6', '#f97316'],
                  borderWidth: 0
              }]
          };
      }

      // 2. Calories Line
      if (n.last_7_days) {
          this.lineChartData = {
              labels: n.last_7_days.map((d: any) => new Date(d.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })),
              datasets: [{
                  data: n.last_7_days.map((d: any) => d.calories),
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
    } catch (e) {
        return dateStr;
    }
  } 
}
