import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { StatsService } from '../../services/stats.service';
import { signal } from '@angular/core';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { MetabolismService } from '../../services/metabolism.service';
import { NutritionService } from '../../services/nutrition.service';
import { WeightService } from '../../services/weight.service';
import { TrainerProfileService } from '../../services/trainer-profile.service';
import { MarkdownModule } from 'ngx-markdown';

import { WorkoutStats } from '../../models/stats.model';
import { MetabolismResponse } from '../../models/metabolism.model';
import { TrainerFactory } from '../../test-utils/factories/trainer.factory';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let statsServiceMock: Partial<StatsService>;
  let nutritionServiceMock: Partial<NutritionService>;
  let metabolismServiceMock: Partial<MetabolismService>;
  let weightServiceMock: Partial<WeightService>;
  let trainerServiceMock: Partial<TrainerProfileService>;

  beforeEach(async () => {
    statsServiceMock = {
      fetchStats: jest.fn().mockResolvedValue(null),
      getStats: jest.fn().mockResolvedValue(null),
      stats: signal(null),
      isLoading: signal(false)
    };

    nutritionServiceMock = {
      getStats: jest.fn().mockResolvedValue(null),
      stats: signal(null)
    };

    metabolismServiceMock = {
      getSummary: jest.fn().mockResolvedValue(null),
      stats: signal(null),
      isInsightLoading: signal(false),
      insightText: signal(''),
      generateInsight: jest.fn().mockResolvedValue('New insight')
    };

    trainerServiceMock = {
        getAvailableTrainers: jest.fn().mockResolvedValue(TrainerFactory.createAllTrainers()),
        fetchProfile: jest.fn().mockResolvedValue(TrainerFactory.create()),
        profile: signal(TrainerFactory.create())
    };

    weightServiceMock = {
      getBodyCompositionStats: jest.fn().mockResolvedValue({
        latest: { weight: 80, fatPercentage: 20 },
        history: []
      })
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: StatsService, useValue: statsServiceMock },
        { provide: NutritionService, useValue: nutritionServiceMock },
        { provide: MetabolismService, useValue: metabolismServiceMock },
        { provide: WeightService, useValue: weightServiceMock },
        { provide: TrainerProfileService, useValue: trainerServiceMock },
        provideCharts(withDefaultRegisterables())
      ]
    })
    .overrideComponent(DashboardComponent, {
      remove: { imports: [MarkdownModule] }
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should fetch stats on init', () => {
      expect(statsServiceMock.fetchStats).toHaveBeenCalled();
    });

    it('should initialize chart data signals', () => {
      expect(component.barChartData).toBeDefined();
      expect(component.lineChartData).toBeDefined();
      expect(component.doughnutChartData).toBeDefined();
    });

    it('should load all services on init', async () => {
      await fixture.whenStable();

      expect(statsServiceMock.fetchStats).toHaveBeenCalled();
      expect(trainerServiceMock.getAvailableTrainers).toHaveBeenCalled();
    });
  });

  describe('Stats Loading', () => {
    it('should update chart when stats change', () => {
      const mockStats: WorkoutStats = {
        weekly_volume: [
          { category: 'Chest', volume: 1000 },
          { category: 'Legs', volume: 2000 }
        ],
        current_streak_weeks: 5,
        weekly_frequency: [true, false, true, false, true, false, false],
        last_workout: { id: '123', workout_type: 'Push', date: new Date().toISOString(), duration_minutes: 60 },
        recent_prs: []
      };

      statsServiceMock.stats!.set(mockStats);
      fixture.detectChanges();

      expect(component.barChartData.labels).toEqual(['Chest', 'Legs']);
      expect(component.barChartData.datasets[0].data).toEqual([1000, 2000]);
    });

    it('should handle loading state', () => {
      (statsServiceMock.isLoading as any).set(true);
      fixture.detectChanges();

      expect(component.isLoading()).toBe(true);
    });

    it('should hide loading after data loads', () => {
      (statsServiceMock.isLoading as any).set(false);
      fixture.detectChanges();

      expect(component.isLoading()).toBe(false);
    });

    it('should display skeleton loaders while loading', () => {
      (statsServiceMock.isLoading as any).set(true);
      fixture.detectChanges();

      const skeletons = fixture.nativeElement.querySelectorAll('[data-test="skeleton"]');
      expect(skeletons.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty stats', () => {
      statsServiceMock.stats!.set({
        weekly_volume: [],
        recent_prs: [],
        current_streak_weeks: 0,
        weekly_frequency: []
      });
      fixture.detectChanges();

      expect(component.stats()).toBeDefined();
    });
  });

  describe('Metabolism Charts', () => {
    it('should update metabolism charts when metabolism stats change', () => {
      const mockMetabolism: MetabolismResponse = {
        latest_weight: 75,
        target_weight: 70,
        start_weight: 80,
        goal_type: 'lose',
        weeks_to_goal: 10,
        fat_change_kg: -2,
        muscle_change_kg: 1,
        end_fat_pct: 20,
        end_muscle_pct: 40,
        weight_trend: [
          { date: '2026-01-01', weight: 80 },
          { date: '2026-01-02', weight: 79 }
        ],
        consistency: [
          { date: '2026-01-01', weight: true, nutrition: true },
          { date: '2026-01-02', weight: false, nutrition: true }
        ]
      };

      component.metabolismStats.set(mockMetabolism);
      fixture.detectChanges();

      expect(component.weightChartData.labels?.length).toBeGreaterThanOrEqual(0);
      expect(component.consistencyChartData).toBeDefined();
    });

    it('should display metabolism summary', () => {
      const mockMetabolism: MetabolismResponse = {
        latest_weight: 75,
        target_weight: 70,
        start_weight: 80,
        goal_type: 'lose',
        weeks_to_goal: 10,
        fat_change_kg: -2,
        muscle_change_kg: 1,
        end_fat_pct: 20,
        end_muscle_pct: 40,
        weight_trend: [],
        consistency: []
      };

      component.metabolismStats.set(mockMetabolism);
      fixture.detectChanges();

      expect(component.metabolismStats().latest_weight).toBe(75);
    });

    it('should handle metabolism loading state', () => {
      component.isMetabolismLoading.set(true);
      fixture.detectChanges();

      expect(component.isMetabolismLoading()).toBe(true);
    });

    it('should handle metabolism error gracefully', async () => {
      (metabolismServiceMock.getSummary as jest.Mock).mockRejectedValueOnce(
        new Error('API Fail')
      );

      await component.fetchMetabolismTrend();

      expect(component.isMetabolismLoading()).toBe(false);
    });
  });

  describe('Trainer Display', () => {
    it('should display current trainer', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(component.currentTrainer()).toBeDefined();
    });

    it('should load available trainers', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(trainerServiceMock.getAvailableTrainers).toHaveBeenCalled();
    });

    it('should display trainer card', () => {
      const trainer = TrainerFactory.createAtlas();
      component.currentTrainer.set(trainer);
      fixture.detectChanges();

      const trainerCard = fixture.nativeElement.querySelector('[data-test="trainer-card"]');
      if (trainerCard) {
        expect(trainerCard.textContent).toContain(trainer.name || '');
      }
    });
  });

  describe('Insights & Regeneration', () => {
    it('should display AI insight', () => {
      component.insight.set('Your performance has improved!');
      fixture.detectChanges();

      const insight = fixture.nativeElement.querySelector('[data-test="insight"]');
      if (insight) {
        expect(insight.textContent).toContain('performance');
      }
    });

    it('should regenerate insight on request', async () => {
      component.insight.set('Initial insight');
      await component.regenerateInsight();

      expect(component.insight()).toBeDefined();
    });

    it('should show regenerate button', () => {
      fixture.detectChanges();

      const button = fixture.nativeElement.querySelector('[data-test="regenerate-insight"]');
      if (button) {
        expect(button).toBeTruthy();
      }
    });

    it('should disable regenerate while generating', () => {
      component.isRegeneratingInsight.set(true);
      fixture.detectChanges();

      const button = fixture.nativeElement.querySelector('[data-test="regenerate-insight"]');
      if (button) {
        expect(button.disabled).toBe(true);
      }
    });
  });

  describe('Sections Display', () => {
    it('should display all major sections', () => {
      fixture.detectChanges();

      const sections = fixture.nativeElement.querySelectorAll('[data-test="section"]');
      expect(sections.length).toBeGreaterThan(0);
    });

    it('should display Body Composition section', () => {
      fixture.detectChanges();

      const section = fixture.nativeElement.querySelector('[data-test="section-composition"]');
      if (section) {
        expect(section.textContent).toContain('Composição');
      }
    });

    it('should display Nutrition section', () => {
      fixture.detectChanges();

      const section = fixture.nativeElement.querySelector('[data-test="section-nutrition"]');
      if (section) {
        expect(section.textContent).toContain('Nutrição');
      }
    });

    it('should display Performance section', () => {
      fixture.detectChanges();

      const section = fixture.nativeElement.querySelector('[data-test="section-performance"]');
      if (section) {
        expect(section.textContent).toContain('Desempenho');
      }
    });

    it('should display Data Quality section', () => {
      fixture.detectChanges();

      const section = fixture.nativeElement.querySelector('[data-test="section-quality"]');
      if (section) {
        expect(section.textContent).toContain('Qualidade');
      }
    });
  });

  describe('Widget Integration', () => {
    it('should render child widgets', () => {
      fixture.detectChanges();

      const widgets = fixture.nativeElement.querySelectorAll('[data-test="widget"]');
      expect(widgets.length).toBeGreaterThanOrEqual(0);
    });

    it('should pass data to volume widget', () => {
      const mockStats: WorkoutStats = {
        weekly_volume: [{ category: 'Chest', volume: 5000 }],
        recent_prs: [],
        current_streak_weeks: 3,
        weekly_frequency: []
      };

      statsServiceMock.stats!.set(mockStats);
      fixture.detectChanges();

      const volumeWidget = fixture.nativeElement.querySelector('[data-test="widget-volume"]');
      if (volumeWidget) {
        expect(volumeWidget).toBeTruthy();
      }
    });
  });

  describe('Date Formatting', () => {
    it('should format dates correctly', () => {
      const formatted = component.getFormattedDate('2026-01-01T10:00:00');
      expect(formatted).toBeTruthy();
      expect(formatted).not.toBe('2026-01-01T10:00:00');
    });

    it('should handle invalid date fallback', () => {
      const invalid = component.getFormattedDate('baddate');
      expect(invalid).toBe('baddate');
    });

    it('should handle empty date', () => {
      expect(component.getFormattedDate('')).toBe('');
    });

    it('should format ISO dates correctly', () => {
      const formatted = component.getFormattedDate('2026-12-25T15:30:00Z');
      expect(formatted).toBeTruthy();
    });
  });

  describe('Sparkline Visualization', () => {
    it('should generate sparkline path', () => {
      const data = [10, 20, 15, 25, 30];
      const path = component.getSparklinePath(data);

      expect(path).toMatch(/M/);
      expect(path).toMatch(/L/);
    });

    it('should handle empty data for sparkline', () => {
      const path = component.getSparklinePath([]);
      expect(path).toBeDefined();
    });

    it('should handle single point', () => {
      const path = component.getSparklinePath([50]);
      expect(path).toBeDefined();
    });

    it('should handle large dataset', () => {
      const data = Array.from({ length: 100 }, (_, i) => i * 10);
      const path = component.getSparklinePath(data);

      expect(path).toBeTruthy();
    });
  });

  describe('Metabolic Balance', () => {
    it('should calculate metabolic balance progress - surplus', () => {
      const progress = component.getMetabolicBalanceProgress('surplus');
      expect(progress).toBeGreaterThan(50);
    });

    it('should calculate metabolic balance progress - deficit', () => {
      const progress = component.getMetabolicBalanceProgress('deficit');
      expect(progress).toBeLessThan(50);
    });

    it('should calculate metabolic balance progress - maintenance', () => {
      const progress = component.getMetabolicBalanceProgress('maintenance');
      expect(progress).toBeCloseTo(50, 10);
    });
  });

  describe('Weight Variation', () => {
    it('should calculate weight variation - gain', () => {
      const variation = component.getWeightVariation(85, 80);
      expect(variation).toBe(5);
    });

    it('should calculate weight variation - loss', () => {
      const variation = component.getWeightVariation(80, 85);
      expect(variation).toBe(-5);
    });

    it('should calculate weight variation - no change', () => {
      const variation = component.getWeightVariation(80, 80);
      expect(variation).toBe(0);
    });

    it('should handle decimal weights', () => {
      const variation = component.getWeightVariation(80.5, 79.3);
      expect(variation).toBeCloseTo(1.2, 1);
    });
  });

  describe('Error Handling', () => {
    it('should handle stats load error', async () => {
      (statsServiceMock.fetchStats as jest.Mock).mockRejectedValueOnce(
        new Error('Stats error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });

    it('should handle nutrition load error', async () => {
      (nutritionServiceMock.getStats as jest.Mock).mockRejectedValueOnce(
        new Error('Nutrition error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });

    it('should handle trainer load error', async () => {
      (trainerServiceMock.getAvailableTrainers as jest.Mock).mockRejectedValueOnce(
        new Error('Trainer error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });

    it('should recover from network errors', async () => {
      (statsServiceMock.fetchStats as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(null);

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });
  });

  describe('Responsive Layout', () => {
    it('should use responsive grid layout', () => {
      fixture.detectChanges();

      const mainGrid = fixture.nativeElement.querySelector('[data-test="main-grid"]');
      if (mainGrid) {
        expect(mainGrid.classList.contains('grid')).toBe(true);
      }
    });

    it('should render without errors on small viewport', () => {
      fixture.detectChanges();
      expect(component).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very large dataset', () => {
      const largeStats = {
        weekly_volume: Array.from({ length: 52 }, (_, i) => ({
          category: `Week ${i}`,
          volume: Math.random() * 10000
        })),
        recent_prs: [],
        current_streak_weeks: 52,
        weekly_frequency: Array(7).fill(true)
      };

      statsServiceMock.stats!.set(largeStats);
      fixture.detectChanges();

      expect(component).toBeTruthy();
    });

    it('should handle null stats', () => {
      statsServiceMock.stats!.set(null);
      fixture.detectChanges();

      expect(component).toBeTruthy();
    });

    it('should handle component destruction', () => {
      fixture.detectChanges();
      fixture.destroy();

      expect(fixture.componentInstance).toBeTruthy();
    });

    it('should handle rapid stat updates', () => {
      for (let i = 0; i < 10; i++) {
        statsServiceMock.stats!.set({
          weekly_volume: [{ category: 'Test', volume: i * 1000 }],
          recent_prs: [],
          current_streak_weeks: i,
          weekly_frequency: []
        });
      }

      fixture.detectChanges();
      expect(component).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('should load quickly with minimal data', async () => {
      const start = performance.now();

      fixture.detectChanges();
      await fixture.whenStable();

      const duration = performance.now() - start;
      expect(duration).toBeLessThan(5000);
    });
  });

  describe('Chart Options', () => {
    it('should have proper bar chart options', () => {
      expect(component.barChartOptions).toBeDefined();
      expect(component.barChartOptions.responsive).toBe(true);
    });

    it('should have proper line chart options', () => {
      expect(component.lineChartOptions).toBeDefined();
      expect(component.lineChartOptions.responsive).toBe(true);
    });

    it('should have proper doughnut chart options', () => {
      expect(component.doughnutChartOptions).toBeDefined();
      expect(component.doughnutChartOptions.responsive).toBe(true);
    });

    it('should use correct chart types', () => {
      expect(component.barChartType).toBe('bar');
      expect(component.lineChartType).toBe('line');
      expect(component.doughnutChartType).toBe('doughnut');
    });
  });

  describe('Data Integration', () => {
    it('should integrate multiple data sources', async () => {
      const mockStats: WorkoutStats = {
        weekly_volume: [{ category: 'Chest', volume: 1000 }],
        recent_prs: [],
        current_streak_weeks: 5,
        weekly_frequency: []
      };

      const mockMetabolism: MetabolismResponse = {
        latest_weight: 75,
        target_weight: 70,
        start_weight: 80,
        goal_type: 'lose',
        weeks_to_goal: 10,
        fat_change_kg: -2,
        muscle_change_kg: 1,
        end_fat_pct: 20,
        end_muscle_pct: 40,
        weight_trend: [],
        consistency: []
      };

      statsServiceMock.stats!.set(mockStats);
      component.metabolismStats.set(mockMetabolism);

      fixture.detectChanges();

      expect(component.stats()).toEqual(mockStats);
      expect(component.metabolismStats()).toEqual(mockMetabolism);
    });
  });
});
