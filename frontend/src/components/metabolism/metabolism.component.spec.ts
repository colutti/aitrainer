import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MetabolismComponent } from './metabolism.component';
import { MetabolismService } from '../../services/metabolism.service';
import { UserProfileService } from '../../services/user-profile.service';
import { NutritionService } from '../../services/nutrition.service';
import { signal, NO_ERRORS_SCHEMA } from '@angular/core';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

describe('MetabolismComponent', () => {
  let component: MetabolismComponent;
  let fixture: ComponentFixture<MetabolismComponent>;
  let metabolismServiceMock: any;
  let userProfileServiceMock: any;
  let nutritionServiceMock: any;

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
      userProfile: signal({ goal_type: 'deficit', weekly_rate: -0.5 } as any),
      getProfile: jest.fn()
    };

    nutritionServiceMock = {
      getStats: jest.fn().mockResolvedValue({} as any)
    };

    await TestBed.configureTestingModule({
      imports: [MetabolismComponent],
      providers: [
        { provide: MetabolismService, useValue: metabolismServiceMock },
        { provide: UserProfileService, useValue: userProfileServiceMock },
        { provide: NutritionService, useValue: nutritionServiceMock },
        provideHttpClient(),
        provideHttpClientTesting()
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
      fixture.detectChanges();
      await fixture.whenStable();

      expect(metabolismServiceMock.getSummary).toHaveBeenCalled();
    });
  });

  describe('Data Fetching', () => {
    it('should load metabolism stats successfully', async () => {
      await component.fetchMetabolismData();

      expect(component.stats()).toEqual(mockMetabolismResponse);
      expect(component.isLoading()).toBe(false);
    });

    it('should handle fetch error gracefully', async () => {
      metabolismServiceMock.getSummary.mockRejectedValueOnce(new Error('API Error'));

      await component.fetchMetabolismData();

      expect(component.stats()).toBeNull();
      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Recommendations', () => {
    it('should generate recommendation with sufficient data', () => {
      component.stats.set(mockMetabolismResponse as any);
      const recommendation = component.getRecommendation();
      expect(recommendation).toContain('2000');
    });
  });

  describe('Progress Calculations', () => {
    it('should calculate progress percentage', () => {
      component.stats.set(mockMetabolismResponse as any);
      const progress = component.getProgressStatus();
      expect(progress.percentage).toBeGreaterThan(0);
    });
  });

  describe('Total Progress Percentage', () => {
    it('should calculate overall progress to goal', () => {
      component.stats.set(mockMetabolismResponse as any);
      const percentage = component.getTotalProgressPercentage();
      expect(percentage).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Chart Data', () => {
    it('should update weight chart with trend data', () => {
      component.stats.set(mockMetabolismResponse as any);
      component.updateWeightChart(mockMetabolismResponse.weight_trend);
      expect(component.weightChartData.labels?.length).toBe(3);
    });
  });

  describe('Metabolic Balance Progress', () => {
    it('should calculate balance progress', () => {
      component.stats.set(mockMetabolismResponse as any);
      const progress = component.getMetabolicBalanceProgress();
      expect(progress).toBeGreaterThanOrEqual(0);
    });
  });
});
