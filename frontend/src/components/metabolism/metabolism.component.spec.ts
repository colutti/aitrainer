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

    it('should update period and refetch data', () => {
      // Mock fetchMetabolismData to avoid actual call/state complexity in this specific test or just spy
      const fetchSpy = jest.spyOn(component, 'fetchMetabolismData');
      
      component.setPeriod(8);
      
      expect(component.weeks()).toBe(8);
      expect(fetchSpy).toHaveBeenCalled();
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

    it('should cap progress at 100%', () => {
      component.stats.set({ ...mockMetabolismResponse, energy_balance: 1000 });

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBeLessThanOrEqual(100);
    });

    it('should floor progress at 0%', () => {
      component.stats.set({ ...mockMetabolismResponse, energy_balance: -1000 });

      const progress = component.getMetabolicBalanceProgress();

      expect(progress).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Progress Status - Branch Coverage', () => {
    it('should return yellow color for 50-89% progress', () => {
      component.stats.set({ ...mockMetabolismResponse, weight_change_per_week: -0.35 }); // ~70% of goal

      const progress = component.getProgressStatus();

      expect(progress.color).toContain('yellow');
      expect(progress.percentage).toBeGreaterThanOrEqual(50);
      expect(progress.percentage).toBeLessThan(90);
    });

    it('should handle null stats in getProgressStatus', () => {
      component.stats.set(null);

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(0);
      expect(progress.label).toBe('--');
      expect(progress.color).toContain('gray');
    });

    it('should handle undefined goal_weekly_rate', () => {
      component.stats.set({ ...mockMetabolismResponse, goal_weekly_rate: undefined });

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(0);
    });

    it('should handle goal_weekly_rate of 0', () => {
      component.stats.set({ ...mockMetabolismResponse, goal_weekly_rate: 0 });

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(0);
    });

    it('should calculate exactly 100% progress', () => {
      component.stats.set({ ...mockMetabolismResponse, weight_change_per_week: -0.5 }); // 100% of goal

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(100);
      expect(progress.color).toContain('green');
    });

    it('should handle negative weight changes correctly', () => {
      component.stats.set({ ...mockMetabolismResponse, weight_change_per_week: -0.25, goal_weekly_rate: -0.5 }); // 50%

      const progress = component.getProgressStatus();

      expect(progress.percentage).toBe(50);
    });
  });

  describe('Total Progress - Edge Cases', () => {
    it('should return 0% when no start_weight', () => {
      component.stats.set({ ...mockMetabolismResponse, start_weight: undefined });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBe(0);
    });

    it('should return 0% when no target_weight', () => {
      component.stats.set({ ...mockMetabolismResponse, target_weight: undefined });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBe(0);
    });

    it('should return 100% when start equals target', () => {
      component.stats.set({ ...mockMetabolismResponse, start_weight: 100, target_weight: 100 });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBe(100);
    });

    it('should clamp at 100%', () => {
      component.stats.set({ ...mockMetabolismResponse, start_weight: 100, target_weight: 80, latest_weight: 70 });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBeLessThanOrEqual(100);
    });

    it('should clamp at 0%', () => {
      component.stats.set({ ...mockMetabolismResponse, start_weight: 100, target_weight: 80, latest_weight: 101 });

      const percentage = component.getTotalProgressPercentage();

      expect(percentage).toBeGreaterThanOrEqual(0);
    });
  });


  describe('Confidence Reason - All Paths', () => {
    it('should handle high confidence with reason', () => {
      const customStats = { ...mockMetabolismResponse, confidence: 'high', confidence_reason: 'Muitos dados' };
      component.stats.set(customStats);

      const reason = component.getConfidenceReason(component.stats());

      expect(reason).toContain('Muitos dados');
    });

    it('should handle low confidence without reason', () => {
      component.stats.set({ ...mockMetabolismResponse, confidence: 'low', confidence_reason: undefined });

      const reason = component.getConfidenceReason(component.stats());

      expect(reason).toContain('Dados inconsistentes');
    });

  });

  describe('Effect & Change Detection', () => {
    it('should mark for check in ngAfterViewInit', () => {
      component.ngAfterViewInit();
      expect(component.cdr).toBeTruthy();
    });
  });

  describe('Recommendation - Confidence None', () => {
    it('should return generic message for confidence none', () => {
      component.stats.set({ ...mockMetabolismResponse, confidence: 'none' });

      const recommendation = component.getRecommendation();

      expect(recommendation).toContain('insuficientes');
      expect(recommendation).toContain('Continue logando');
    });
  });
});
