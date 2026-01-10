import { Component, inject, OnInit, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { StatsService } from '../../services/stats.service';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { VolumeStat } from '../../models/stats.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  statsService = inject(StatsService);
  stats = this.statsService.stats;
  isLoading = this.statsService.isLoading;

  // Chart Config
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

  constructor() {
    effect(() => {
      const s = this.stats();
      if (s?.weekly_volume) {
        this.updateChart(s.weekly_volume);
      }
    });
  }

  ngOnInit() {
    this.statsService.fetchStats();
  }

  updateChart(volumeStats: VolumeStat[]) {
    // Only take top 5 categories to avoid clutter
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

  protected readonly Array = Array; // For template usage if needed
}
