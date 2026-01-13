import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WeightService } from '../../services/weight.service';
import { WeightLog, BodyCompositionStats } from '../../models/weight-log.model';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { NumericInputDirective } from '../../directives/numeric-input.directive';

@Component({
  selector: 'app-body-composition',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, FormsModule, NumericInputDirective],
  templateUrl: './body-composition.component.html'
})
export class BodyCompositionComponent implements OnInit {
  weightService = inject(WeightService);
  
  stats = signal<BodyCompositionStats | null>(null);
  history = signal<WeightLog[]>([]);
  isLoading = signal(true);

  // Manual Entry Form Signals
  entryDate = signal<string>(new Date().toISOString().split('T')[0]);
  entryWeight = signal<number | null>(null);
  entryFat = signal<number | null>(null);
  entryMuscle = signal<number | null>(null);
  entryWater = signal<number | null>(null);
  entryVisceral = signal<number | null>(null);
  entryBmr = signal<number | null>(null);
  isSavingEntry = signal(false);
  showSuccessMessage = signal(false);

  // Charts
  lineChartType: ChartConfiguration['type'] = 'line';
  
  weightChartData: ChartConfiguration['data'] = { datasets: [], labels: [] };
  fatChartData: ChartConfiguration['data'] = { datasets: [], labels: [] };
  muscleChartData: ChartConfiguration['data'] = { datasets: [], labels: [] }; // Added muscle chart
  
  chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    elements: { line: { tension: 0.4 } },
    scales: {
        y: { display: true, grid: { color: 'rgba(255,255,255,0.05)' } },
        x: { display: false }
    },
    plugins: { legend: { display: false } }
  };

  async ngOnInit() {
    await this.loadData();
  }

  async loadData() {
    this.isLoading.set(true);
    try {
        const [stats, history] = await Promise.all([
          this.weightService.getBodyCompositionStats(),
          this.weightService.getHistory()
        ]);
        
        this.stats.set(stats);
        this.history.set(history);
        
        if (stats) {
           this.setupCharts(stats);
        }
    } catch (e) {
        console.error(e);
    } finally {
        this.isLoading.set(false);
    }
  }

  editEntry(log: WeightLog) {
    this.entryDate.set(log.date);
    this.entryWeight.set(log.weight_kg);
    this.entryFat.set(log.body_fat_pct || null);
    this.entryMuscle.set(log.muscle_mass_pct || null);
    this.entryWater.set(log.body_water_pct || null);
    this.entryVisceral.set(log.visceral_fat || null);
    this.entryBmr.set(log.bmr || null);
    
    // Scroll to top to see form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async deleteEntry(log: WeightLog) {
    if (!confirm(`Tem certeza que deseja excluir o registro de ${log.date}?`)) {
      return;
    }

    this.isLoading.set(true);
    try {
      await this.weightService.deleteWeight(log.date);
      await this.loadData();
    } catch (e) {
      console.error('Failed to delete entry', e);
    } finally {
      this.isLoading.set(false);
    }
  }

  async saveEntry() {
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

      // Clear form (except date maybe? let's keep date)
      this.entryWeight.set(null);
      this.entryFat.set(null);
      this.entryMuscle.set(null);
      this.entryWater.set(null);
      this.entryVisceral.set(null);
      this.entryBmr.set(null);
      
      this.showSuccessMessage.set(true);
      setTimeout(() => this.showSuccessMessage.set(false), 3000);

      // Reload data
      await this.loadData();

    } catch (e) {
      console.error('Failed to save entry', e);
    } finally {
      this.isSavingEntry.set(false);
    }
  }

  setupCharts(stats: BodyCompositionStats) {
    // Weight Chart
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
    
    // Fat Chart
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

    // Muscle Chart
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
}
