import { Component, OnInit, AfterViewInit, ChangeDetectorRef, inject, signal, effect, NgZone } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WeightService } from '../../services/weight.service';
import { NutritionService } from '../../services/nutrition.service';
import { MetabolismService } from '../../services/metabolism.service';
import { WeightLog, BodyCompositionStats } from '../../models/weight-log.model';
import { NutritionLog, NutritionStats } from '../../models/nutrition.model';
import { MetabolismResponse } from '../../models/metabolism.model';
import { ChartConfiguration, ChartData } from 'chart.js';
import { DateInputComponent } from '../shared/date-input/date-input.component';
import { AppDateFormatPipe } from '../../pipes/date-format.pipe';
import { AppNumberFormatPipe } from '../../pipes/number-format.pipe';

// Weight Tab Widgets
import { WidgetBodyEvolutionComponent } from '../widgets/widget-body-evolution.component';
import { WidgetLineChartComponent } from '../widgets/widget-line-chart.component';

// Nutrition Tab Widgets
import { WidgetMacrosTodayComponent } from '../widgets/widget-macros-today.component';
import { WidgetMacroTargetsComponent } from '../widgets/widget-macro-targets.component';
import { WidgetCalorieHistoryComponent } from '../widgets/nutrition/widget-calorie-history.component';

// Metabolism Tab Widgets
import { WidgetTdeeSummaryComponent } from '../widgets/widget-tdee-summary.component';
import { WidgetMetabolicGaugeComponent } from '../widgets/widget-metabolic-gauge.component';
import { WidgetCaloriesWeightComparisonComponent } from '../widgets/widget-calories-weight-comparison.component';

// Shared Input Components
import { NumberInputComponent } from '../shared/number-input/number-input.component';

type BodyTab = 'peso' | 'nutricao' | 'medidas' | 'estatisticas';

@Component({
  selector: 'app-body',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DateInputComponent,
    AppDateFormatPipe,
    AppNumberFormatPipe,
    // Weight
    WidgetBodyEvolutionComponent,
    WidgetLineChartComponent,
    // Nutrition
    WidgetMacrosTodayComponent,
    WidgetMacroTargetsComponent,
    WidgetCalorieHistoryComponent,
    // Metabolism
    WidgetTdeeSummaryComponent,
    WidgetMetabolicGaugeComponent,
    WidgetCaloriesWeightComparisonComponent,
    // Input Components
    NumberInputComponent,
  ],
  templateUrl: './body.component.html',
  providers: [DatePipe]
})
export class BodyComponent implements OnInit, AfterViewInit {
  private weightService = inject(WeightService);
  private nutritionService = inject(NutritionService);
  private metabolismService = inject(MetabolismService);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private datePipe = inject(DatePipe);

  // Tab Control
  activeTab = signal<BodyTab>('estatisticas');

  // === PESO TAB ===
  weightStats = signal<BodyCompositionStats | null>(null);
  weightHistory = signal<WeightLog[]>([]);
  weightIsLoading = signal(true);

  // Weight Entry Form
  entryDate = signal<string>(new Date().toISOString().split('T')[0]);
  entryWeight = signal<number | null>(null);
  entryFat = signal<number | null>(null);
  entryMuscle = signal<number | null>(null);
  entryWater = signal<number | null>(null);
  entryVisceral = signal<number | null>(null);
  entryBmr = signal<number | null>(null);
  isSavingEntry = signal(false);
  showSuccessMessage = signal(false);

  // Weight Charts
  lineChartType: ChartConfiguration['type'] = 'line';
  weightChartData: ChartConfiguration['data'] = { datasets: [], labels: [] };
  fatChartData: ChartConfiguration['data'] = { datasets: [], labels: [] };
  muscleChartData: ChartConfiguration['data'] = { datasets: [], labels: [] };
  chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    elements: { line: { tension: 0.4 } },
    scales: {
      y: {
        display: true,
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { callback: (value) => Number(value).toFixed(1) }
      },
      x: { display: false }
    },
    plugins: { legend: { display: false } }
  };

  fatChartOptions: ChartConfiguration['options'] = {
    ...this.chartOptions,
    scales: { ...this.chartOptions?.scales, y: { ...this.chartOptions?.scales?.['y'], ticks: { callback: (v) => `${v}%` } } }
  };

  muscleChartOptions = this.fatChartOptions;

  // === NUTRIÇÃO TAB ===
  nutritionLogs = signal<NutritionLog[]>([]);
  nutritionStats = signal<NutritionStats | null>(null);
  nutritionIsLoading = signal(true);
  nutritionCurrentPage = signal(1);
  nutritionTotalPages = signal(1);
  nutritionDaysFilter = signal<number | undefined>(undefined);

  // Nutrition Entry Form
  entryNutritionDate = signal<string>(new Date().toISOString().split('T')[0]);
  entryNutritionSource = signal<string>('Manual');
  entryNutritionCalories = signal<number | null>(null);
  entryNutritionProtein = signal<number | null>(null);
  entryNutritionCarbs = signal<number | null>(null);
  entryNutritionFat = signal<number | null>(null);
  isSavingNutrition = signal(false);
  showNutritionSuccess = signal(false);

  // === MEDIDAS TAB ===
  metabolismStats = signal<MetabolismResponse | null>(null);
  metabolismIsLoading = signal(true);
  metabolismWeeks = signal<number>(3);
  metabolismPeriods = [2, 4, 8, 12];

  weightChartDataMetabolism: ChartConfiguration['data'] = { labels: [], datasets: [] };
  weightChartOptionsMetabolism: ChartConfiguration['options'] = {
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

  constructor() {
    // Update weight charts when stats change
    effect(() => {
      const s = this.weightStats();
      if (s) {
        this.setupWeightCharts(s);
        this.cdr.markForCheck();
      }
    });

    // Update metabolism chart when stats change
    effect(() => {
      const s = this.metabolismStats();
      if (s && s.weight_trend) {
        this.updateMetabolismWeightChart(s.weight_trend);
        this.cdr.markForCheck();
      }
    });
  }

  async ngOnInit() {
    await this.loadAllData();
  }

  ngAfterViewInit() {
    this.cdr.markForCheck();
  }

  switchTab(tab: BodyTab) {
    this.activeTab.set(tab);
  }

  private async loadAllData() {
    // Load all tabs data in parallel
    await Promise.all([
      this.loadWeightData(),
      this.loadNutritionData(),
      this.loadMetabolismData()
    ]);
  }

  // ===== PESO TAB METHODS =====

  private async loadWeightData() {
    this.weightIsLoading.set(true);
    try {
      const [stats, history] = await Promise.all([
        this.weightService.getBodyCompositionStats(),
        this.weightService.getHistory()
      ]);

      this.ngZone.run(() => {
        this.weightStats.set(stats);
        this.weightHistory.set(history);
        this.weightIsLoading.set(false);
        this.cdr.detectChanges();
      });
    } catch (e) {
      this.ngZone.run(() => {
        this.weightIsLoading.set(false);
        this.cdr.detectChanges();
      });
    }
  }

  editWeightEntry(log: WeightLog) {
    this.entryDate.set(log.date);
    this.entryWeight.set(log.weight_kg);
    this.entryFat.set(log.body_fat_pct || null);
    this.entryMuscle.set(log.muscle_mass_pct || null);
    this.entryWater.set(log.body_water_pct || null);
    this.entryVisceral.set(log.visceral_fat || null);
    this.entryBmr.set(log.bmr || null);
    this.cdr.detectChanges();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async deleteWeightEntry(log: WeightLog) {
    if (!confirm(`Tem certeza que deseja excluir o registro de ${log.date}?`)) {
      return;
    }

    this.weightIsLoading.set(true);
    try {
      await this.weightService.deleteWeight(log.date);
      await this.loadWeightData();
    } catch (e) {
      this.weightIsLoading.set(false);
    }
  }

  async saveWeightEntry() {
    if (!this.entryWeight()) return;

    this.isSavingEntry.set(true);
    try {
      await this.weightService.logWeight(this.entryWeight()!, {
        date: this.entryDate(),
        body_fat_pct: this.entryFat() || undefined,
        muscle_mass_pct: this.entryMuscle() || undefined,
        body_water_pct: this.entryWater() || undefined,
        visceral_fat: this.entryVisceral() || undefined,
        bmr: this.entryBmr() || undefined
      });

      this.entryWeight.set(null);
      this.entryFat.set(null);
      this.entryMuscle.set(null);
      this.entryWater.set(null);
      this.entryVisceral.set(null);
      this.entryBmr.set(null);

      this.showSuccessMessage.set(true);
      setTimeout(() => this.showSuccessMessage.set(false), 3000);

      await this.loadWeightData();
    } catch (e) {
    } finally {
      this.isSavingEntry.set(false);
    }
  }

  private setupWeightCharts(stats: BodyCompositionStats) {
    this.weightChartData = {
      labels: stats.weight_trend.map(d => d.date),
      datasets: [{
        data: stats.weight_trend.map(d => d.value),
        borderColor: '#ffffff',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 4
      }]
    };

    this.fatChartData = {
      labels: stats.fat_trend.map(d => d.date),
      datasets: [{
        data: stats.fat_trend.map(d => d.value),
        borderColor: '#f97316',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        fill: true,
        pointRadius: 2
      }]
    };

    this.muscleChartData = {
      labels: stats.muscle_trend.map(d => d.date),
      datasets: [{
        data: stats.muscle_trend.map(d => d.value),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        pointRadius: 2
      }]
    };
  }

  // ===== NUTRIÇÃO TAB METHODS =====

  private async loadNutritionData() {
    this.nutritionIsLoading.set(true);
    try {
      const [stats] = await Promise.all([
        this.nutritionService.getStats(),
        this.loadNutritionLogs()
      ]);

      this.ngZone.run(() => {
        this.nutritionStats.set(stats || null);
        this.nutritionIsLoading.set(false);
        this.cdr.markForCheck();
      });
    } catch (e) {
      this.ngZone.run(() => {
        this.nutritionIsLoading.set(false);
      });
    }
  }

  private async loadNutritionLogs() {
    try {
      const response = await this.nutritionService.getLogs(this.nutritionCurrentPage(), 10, this.nutritionDaysFilter());
      this.nutritionLogs.set(response.logs);
      this.nutritionTotalPages.set(response.total_pages);
    } catch {
      // Error handling
    }
  }

  nextNutritionPage() {
    if (this.nutritionCurrentPage() < this.nutritionTotalPages()) {
      this.nutritionCurrentPage.update(p => p + 1);
      this.loadNutritionLogs();
    }
  }

  prevNutritionPage() {
    if (this.nutritionCurrentPage() > 1) {
      this.nutritionCurrentPage.update(p => p - 1);
      this.loadNutritionLogs();
    }
  }

  async deleteNutritionLog(event: Event, log: NutritionLog) {
    event.stopPropagation();
    if (confirm('Tem certeza que deseja excluir este registro nutricional?')) {
      try {
        await this.nutritionService.deleteLog(log.id);
        this.nutritionCurrentPage.set(1);
        await this.loadNutritionData();
      } catch {
        // Error handling
      }
    }
  }

  async saveNutritionEntry() {
    if (!this.entryNutritionCalories()) return;

    this.isSavingNutrition.set(true);
    try {
      await this.nutritionService.logNutrition({
        date: this.entryNutritionDate(),
        source: this.entryNutritionSource(),
        calories: this.entryNutritionCalories()!,
        protein_grams: this.entryNutritionProtein() || 0,
        carbs_grams: this.entryNutritionCarbs() || 0,
        fat_grams: this.entryNutritionFat() || 0
      });

      this.entryNutritionDate.set(new Date().toISOString().split('T')[0]);
      this.entryNutritionSource.set('Manual');
      this.entryNutritionCalories.set(null);
      this.entryNutritionProtein.set(null);
      this.entryNutritionCarbs.set(null);
      this.entryNutritionFat.set(null);

      this.showNutritionSuccess.set(true);
      setTimeout(() => this.showNutritionSuccess.set(false), 3000);

      this.nutritionCurrentPage.set(1);
      await this.loadNutritionData();
    } catch (e) {
    } finally {
      this.isSavingNutrition.set(false);
    }
  }

  getNutritionMacroPercentage(grams: number, type: 'protein' | 'carbs' | 'fat', calories: number): string {
    if (!calories) return '0%';
    const caloriesPerGram = type === 'fat' ? 9 : 4;
    const percentage = Math.round(((grams * caloriesPerGram) / calories) * 100);
    return `${percentage}%`;
  }

  // ===== MEDIDAS TAB METHODS =====

  private async loadMetabolismData() {
    this.metabolismIsLoading.set(true);
    try {
      const data = await this.metabolismService.getSummary(this.metabolismWeeks());
      this.ngZone.run(() => {
        this.metabolismStats.set(data);
        this.metabolismIsLoading.set(false);
        this.cdr.markForCheck();
      });
    } catch (error) {
      this.ngZone.run(() => {
        this.metabolismIsLoading.set(false);
      });
    }
  }

  setMetabolismPeriod(weeks: number) {
    this.metabolismWeeks.set(weeks);
    this.loadMetabolismData();
  }

  getMetabolismRecommendation(): string {
    const s = this.metabolismStats();
    if (!s || s.confidence === 'none') return 'Dados insuficientes. Continue logando peso e dieta.';
    return `Sua meta diária recomendada é de ${s.daily_target} kcal para atingir seu objetivo.`;
  }

  private updateMetabolismWeightChart(trend: any[]) {
    const labels = trend.map(t => this.datePipe.transform(new Date(t.date), 'dd MMM'));
    this.weightChartDataMetabolism = {
      labels,
      datasets: [
        { data: trend.map(t => t.weight), borderColor: 'rgba(16, 185, 129, 0.3)', backgroundColor: 'transparent', fill: false, borderWidth: 1, pointRadius: 2, label: 'Real' },
        { data: trend.map(t => t.trend ?? null), borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, borderWidth: 3, pointRadius: 0, label: 'Tendência', tension: 0.4 }
      ]
    };
  }
}
