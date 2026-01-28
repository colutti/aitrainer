import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MetabolismComponent } from './metabolism.component';
import { MetabolismService } from '../../services/metabolism.service';
import { UserProfileService } from '../../services/user-profile.service';
import { NutritionService } from '../../services/nutrition.service';
import { signal, NO_ERRORS_SCHEMA } from '@angular/core';
import { of } from 'rxjs';

describe('MetabolismComponent', () => {
  let component: MetabolismComponent;
  let fixture: ComponentFixture<MetabolismComponent>;
  let metabolismServiceMock: Partial<MetabolismService>;
  let userProfileServiceMock: Partial<UserProfileService>;
  let nutritionServiceMock: Partial<NutritionService>;

  const mockMetabolismResponse = {
    tdee: 2500,
    bmr: 1800,
    daily_target: 2000,
    goal_weekly_rate: -0.5,
    weight_change_per_week: -0.4,
    start_weight: 100,
    target_weight: 80,
    latest_weight: 95,
    confidence: 'high' as const,
    confidence_reason: 'Dados suficientes',
    energy_balance: -200,
    weight_trend: [
      { date: '2026-01-20', weight: 95.0, trend: 94.8 },
      { date: '2026-01-21', weight: 94.9, trend: 94.7 },
      { date: '2026-01-22', weight: 94.8, trend: 94.6 }
    ]
  };

  beforeEach(async () => {
    metabolismServiceMock = {
      getSummary: jest.fn().mockResolvedValue(mockMetabolismResponse)
    };

    userProfileServiceMock = {
      userProfile: signal({ goal_type: 'deficit', weekly_rate: -0.5 }),
      getProfile: jest.fn()
    };

    nutritionServiceMock = {
      getStats: jest.fn().mockReturnValue(of({}))
    };

    await TestBed.configureTestingModule({
      imports: [MetabolismComponent],
      providers: [
        { provide: MetabolismService, useValue: metabolismServiceMock },
        { provide: UserProfileService, useValue: userProfileServiceMock },
        { provide: NutritionService, useValue: nutritionServiceMock }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(MetabolismComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should fetch metabolism data on init', async () => {
      await component.ngOnInit();

      expect(metabolismServiceMock.getSummary).toHaveBeenCalledWith(3);
    });

    it('should load user profile on init', async () => {
      await component.ngOnInit();

      expect(userProfileServiceMock.getProfile).toHaveBeenCalled();
    });

    it('should load nutrition stats on init', async () => {
      await component.ngOnInit();

      expect(nutritionServiceMock.getStats).toHaveBeenCalled();
    });

    it('should initialize with loading state', () => {
      expect(component.isLoading()).toBe(false);
      expect(component.stats()).toBeNull();
    });
  });

  describe('Data Fetching', () => {
    it('should load metabolism stats successfully', async () => {
      await component.fetchMetabolismData();

      expect(component.stats()).toEqual(mockMetabolismResponse);
      expect(component.isLoading()).toBe(false);
    });

    it('should set isLoading during fetch', async () => {
      const promise = component.fetchMetabolismData();
      expect(component.isLoading()).toBe(true);

      await promise;
      expect(component.isLoading()).toBe(false);
    });

    it('should handle fetch error gracefully', async () => {
      (metabolismServiceMock.getSummary as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

      await component.fetchMetabolismData();

      expect(component.stats()).toBeNull();
      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Recommendations', () => {
    it('should generate recommendation with sufficient data', async () => {
      component.stats.set(mockMetabolismResponse);

      const recommendation = component.getRecommendation();

      expect(recommendation).toContain('2000');
      expect(recommendation).toContain('kcal');
    });

    it('should show generic message with insufficient data', () => {
      component.stats.set({ ...mockMetabolismResponse, confidence: 'none' });

      const recommendation = component.getRecommendation();

      expect(recommendation).toContain('insuficientes');
    });

    it('should handle null stats', () => {
      component.stats.set(null);

      const recommendation = component.getRecommendation();

      expect(recommendation).toBeTruthy();
    });
  });

  describe('Progress Calculations', () => {
    it('should calculate progress percentage', () => {
      component.stats.set(mockMetabolismResponse);

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBeGreaterThan(0);
      expect(progress.percentage).toBeLessThanOrEqual(100);
      expect(progress.label).toBeTruthy();
      expect(progress.color).toBeTruthy();
    });

    it('should show green status for 90%+ progress', () => {
      component.stats.set({ ...mockMetabolismResponse, weight_change_per_week: -0.45 }); // 90% of goal

      const progress = component.getProgressStatus();

      expect(progress.color).toContain('green');
    });

    it('should show red status for low progress', () => {
      component.stats.set({ ...mockMetabolismResponse, weight_change_per_week: -0.1 }); // <50% of goal

      const progress = component.getProgressStatus();

      expect(progress.color).toContain('red');
    });

    it('should handle zero goal', () => {
      component.stats.set({ ...mockMetabolismResponse, goal_weekly_rate: 0 });

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(0);
    });
  });

  describe('Total Progress Percentage', () => {
    it('should calculate overall progress to goal', () => {
      component.stats.set(mockMetabolismResponse);

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBeGreaterThanOrEqual(0);
      expect(percentage).toBeLessThanOrEqual(100);
    });

    it('should return 100% when at goal', () => {
      component.stats.set({ ...mockMetabolismResponse, latest_weight: 80 });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBe(100);
    });

    it('should return 0% with no data', () => {
      component.stats.set(null);

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBe(0);
    });

    it('should calculate midpoint progress correctly', () => {
      component.stats.set({ ...mockMetabolismResponse, latest_weight: 90 }); // Halfway to goal (100 -> 80, now 90)

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBeCloseTo(50, 0);
    });
  });

  describe('Confidence Colors', () => {
    it('should return green for high confidence', () => {
      expect(component.getConfidenceColor('high')).toContain('green');
    });

    it('should return yellow for medium confidence', () => {
      expect(component.getConfidenceColor('medium')).toContain('yellow');
    });

    it('should return red for low confidence', () => {
      expect(component.getConfidenceColor('low')).toContain('red');
    });

    it('should return gray for unknown confidence', () => {
      expect(component.getConfidenceColor('unknown')).toContain('gray');
    });

    it('should return hex color correctly', () => {
      expect(component.getConfidenceColorHex('high')).toBe('#4ade80');
      expect(component.getConfidenceColorHex('medium')).toBe('#facc15');
      expect(component.getConfidenceColorHex('low')).toBe('#f87171');
    });
  });

  describe('Confidence Reasoning', () => {
    it('should provide reason for low confidence', () => {
      component.stats.set({ ...mockMetabolismResponse, confidence: 'low' });

      const reason = component.getConfidenceReason(component.stats());

      expect(reason).toBeTruthy();
    });

    it('should provide generic reason with no data', () => {
      const reason = component.getConfidenceReason(null);

      expect(reason).toContain('Dados');
    });

    it('should use custom reason if provided', () => {
      const customStats = { ...mockMetabolismResponse, confidence_reason: 'Custom reason' };
      component.stats.set(customStats);

      const reason = component.getConfidenceReason(component.stats());

      expect(reason).toContain('Custom reason');
    });
  });

  describe('Chart Data', () => {
    it('should update weight chart with trend data', () => {
      component.stats.set(mockMetabolismResponse);

      const initialDatasets = component.weightChartData.datasets[0].data;

      component.updateWeightChart(mockMetabolismResponse.weight_trend);

      expect(component.weightChartData.labels?.length).toBe(3);
      expect(component.weightChartData.datasets[0].data.length).toBe(3);
      expect(component.weightChartData.datasets[1].data.length).toBe(3);
    });

    it('should format chart labels correctly', () => {
      component.stats.set(mockMetabolismResponse);

      component.updateWeightChart(mockMetabolismResponse.weight_trend);

      expect(component.weightChartData.labels).toBeTruthy();
      expect(component.weightChartData.labels?.length).toBe(3);
    });
  });

  describe('Metabolic Balance Progress', () => {
    it('should calculate balance progress', () => {
      component.stats.set(mockMetabolismResponse);

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBeGreaterThanOrEqual(0);
      expect(progress).toBeLessThanOrEqual(100);
    });

    it('should default to 50% without data', () => {
      component.stats.set(null);

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBe(50);
    });

    it('should handle positive energy balance', () => {
      component.stats.set({ ...mockMetabolismResponse, energy_balance: 500 });

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBeGreaterThan(50);
    });

    it('should handle negative energy balance', () => {
      component.stats.set({ ...mockMetabolismResponse, energy_balance: -500 });

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBeLessThan(50);
    });
  });
});
