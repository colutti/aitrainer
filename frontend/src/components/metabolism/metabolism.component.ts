import { Component, inject, OnInit, effect, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { MetabolismService } from "../../services/metabolism.service";
import { UserProfileService } from "../../services/user-profile.service";
import { NutritionService } from "../../services/nutrition.service";
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { WidgetMetabolicGaugeComponent } from '../widgets/widget-metabolic-gauge.component';
import { WidgetLineChartComponent } from '../widgets/widget-line-chart.component';
import { WidgetCaloriesWeightComparisonComponent } from '../widgets/widget-calories-weight-comparison.component';
import { WidgetTdeeSummaryComponent } from '../widgets/widget-tdee-summary.component';

@Component({
  selector: 'app-metabolism',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, WidgetMetabolicGaugeComponent, WidgetLineChartComponent, WidgetCaloriesWeightComparisonComponent, WidgetTdeeSummaryComponent],
  templateUrl: './metabolism.component.html',
})
export class MetabolismComponent implements OnInit {
  metabolismService = inject(MetabolismService);
  userProfileService = inject(UserProfileService);
  nutritionService = inject(NutritionService);
  
  stats = this.metabolismService.stats;
  isLoading = this.metabolismService.isLoading;
  profile = this.userProfileService.userProfile;

  // --- Weight Trend Chart (Mirrored from Home) ---
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
        callbacks: { label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toFixed(1)} kg` }
      },
      legend: {
        display: true,
        position: 'bottom',
        labels: { color: '#a1a1aa', boxWidth: 8, usePointStyle: true, pointStyle: 'circle', font: { size: 9 } }
      }
    },
    scales: {
      x: { ticks: { color: '#a1a1aa', font: { family: 'Inter', size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 7 }, grid: { display: false } },
      y: { ticks: { color: '#a1a1aa', font: { family: 'Inter', size: 10 }, callback: (value) => `${Number(value).toFixed(1)}kg` }, grid: { color: 'rgba(39, 39, 42, 0.5)' }, beginAtZero: false }
    },
    elements: { point: { radius: 3, hoverRadius: 5, backgroundColor: '#10b981', borderWidth: 0 }, line: { tension: 0.3 } }
  };
  public weightChartType: ChartType = 'line';
  public weightChartData: ChartData<'line'> = {
    labels: [],
    datasets: [
        { data: [], borderColor: 'rgba(16, 185, 129, 0.3)', backgroundColor: 'transparent', fill: false, borderWidth: 1, pointRadius: 2, label: 'Real' },
        { data: [], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, borderWidth: 3, pointRadius: 0, label: 'Tendência', tension: 0.4 }
    ]
  };

  constructor() {
      effect(() => {
          const s = this.stats();
          if (s) {
             if (s.weight_trend) {
                this.updateWeightChart(s.weight_trend);
             }
          }
      });
  }

  ngOnInit() {
    this.metabolismService.fetchSummary(3);
    this.userProfileService.getProfile();
    this.nutritionService.getStats().subscribe();
  }
  

  getRecommendation(): string {
    const s = this.stats();
    if (!s || s.confidence === 'none') return 'Dados insuficientes. Continue logando peso e dieta.';
    return `Sua meta diária recomendada é de ${s.daily_target} kcal para atingir seu objetivo.`;
  }

  getProgressStatus(): { percentage: number, label: string, color: string } {
    const s = this.stats();
    if (!s || !s.goal_weekly_rate || s.goal_weekly_rate === 0) return { percentage: 0, label: '--', color: 'bg-gray-500' };

    const actual = Math.abs(s.weight_change_per_week);
    const goal = Math.abs(s.goal_weekly_rate);
    const percentage = Math.min(100, Math.round((actual / goal) * 100));

    let label = `${percentage}% do objetivo`;
    let color = 'bg-yellow-500';

    if (percentage >= 90) {
      label = "No caminho certo! 🎯";
      color = 'bg-green-500';
    } else if (percentage < 50) {
      label = "Abaixo do esperado";
      color = 'bg-red-500';
    }

    return { percentage, label, color };
  }
  
  getConfidenceColor(level: string): string {
    switch(level) {
        case 'high': return 'text-green-400';
        case 'medium': return 'text-yellow-400';
        case 'low': return 'text-red-400';
        default: return 'text-gray-400';
    }
  }

  getConfidenceColorHex(level: string | undefined): string {
      switch(level) {
          case 'high': return '#4ade80';
          case 'medium': return '#facc15';
          case 'low': return '#f87171';
          default: return '#9ca3af';
      }
  }

  getConfidenceReason(s: any): string {
      if (!s) return 'Dados carregando...';
      if (s.confidence === 'low') {
          return s.confidence_reason || 'Dados inconsistentes.';
      }
      return s.confidence_reason || 'Dados confiáveis.';
  }

  getTotalProgressPercentage(): number {
    const s = this.stats();
    if (!s || !s.target_weight || !s.start_weight) return 0;
    
    const totalToChange = Math.abs(s.start_weight - s.target_weight);
    if (totalToChange === 0) return 100;
    
    const currentChange = Math.abs(s.start_weight - s.latest_weight);
    const percentage = (currentChange / totalToChange) * 100;
    
    return Math.min(100, Math.max(0, percentage));
  }

  updateWeightChart(trend: any[]) {
     const labels = trend.map(t => new Date(t.date).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }));
     this.weightChartData = {
       labels,
       datasets: [
         { ...this.weightChartData.datasets[0], data: trend.map(t => t.weight) },
         { ...this.weightChartData.datasets[1], data: trend.map(t => t.trend ?? null) }
       ]
     };
  }

  getMetabolicBalanceProgress(): number {
    const s = this.stats();
    if (!s || !s.energy_balance) return 50; 
    const balance = s.energy_balance;
    const progress = ((balance + 500) / 1000) * 100;
    return Math.min(100, Math.max(0, progress));
  }
}
