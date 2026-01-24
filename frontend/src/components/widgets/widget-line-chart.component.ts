import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';

@Component({
  selector: 'app-widget-line-chart',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="bg-light-bg p-4 rounded-2xl border border-secondary shadow-lg hover:border-primary/50 transition-colors duration-300 flex flex-col">
      <div class="flex justify-between items-start mb-4">
        <div>
          <p class="text-text-secondary text-[10px] font-bold uppercase tracking-wider">{{ title }}</p>
          <div class="text-[10px] text-text-secondary font-bold uppercase tracking-tighter opacity-60" *ngIf="startDate && endDate">
            Período: {{ startDate | date:'dd/MM' }} a {{ endDate | date:'dd/MM' }}
          </div>
          <p class="text-xs text-text-secondary opacity-60 mt-0.5" *ngIf="!startDate && subtitle">{{ subtitle }}</p>
        </div>
        <slot name="header-action"></slot>
      </div>
      
      <div class="flex-1 min-h-[120px] relative mt-2">
        <canvas baseChart [data]="chartData" [options]="options" [type]="type"></canvas>
      </div>
      
      <div class="mt-4 pt-4 border-t border-secondary/30" *ngIf="footerLabel">
        <div class="flex justify-between items-center">
            <span class="text-[9px] text-text-secondary uppercase font-bold tracking-tighter">{{ footerLabel }}</span>
            <slot name="footer-value"></slot>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WidgetLineChartComponent {
  @Input({ required: true }) title: string = '';
  @Input() subtitle: string = '';
  @Input() startDate?: string;
  @Input() endDate?: string;
  @Input() footerLabel?: string;
  @Input({ required: true }) chartData: ChartData<'line'> = { labels: [], datasets: [] };
  
  @Input() type: ChartType = 'line';
  @Input() options: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: { color: '#a1a1aa', boxWidth: 8, usePointStyle: true, pointStyle: 'circle', font: { size: 9 } }
      }
    },
    scales: {
      x: { ticks: { color: '#a1a1aa', font: { size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 7 }, grid: { display: false } },
      y: { ticks: { color: '#a1a1aa', font: { size: 10 } }, grid: { color: 'rgba(39, 39, 42, 0.5)' }, beginAtZero: false }
    }
  };
}
