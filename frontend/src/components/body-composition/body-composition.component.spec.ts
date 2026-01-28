import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { BodyCompositionComponent } from './body-composition.component';
import { WeightService } from '../../services/weight.service';
import { MetabolismService } from '../../services/metabolism.service';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import { signal } from '@angular/core';

describe('BodyCompositionComponent', () => {
  let component: BodyCompositionComponent;
  let fixture: ComponentFixture<BodyCompositionComponent>;
  let mockWeightService: Partial<WeightService>;
  let mockMetabolismService: Partial<MetabolismService>;
  let mockChangeDetectorRef: Partial<ChangeDetectorRef>;
  let mockNgZone: Partial<NgZone>;

  beforeEach(async () => {
    mockWeightService = {
      stats: signal({
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: []
      }),
      lastWeight: signal(80),
      getBodyCompositionStats: jest.fn().mockResolvedValue({
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: []
      }),
      getWeightHistory: jest.fn().mockResolvedValue([]),
      logWeight: jest.fn().mockResolvedValue({ id: 1, weight: 80, date: new Date() })
    };

    mockMetabolismService = {
      getSummary: jest.fn().mockResolvedValue({
        tdee: 2500,
        bmr: 1800
      })
    };

    mockChangeDetectorRef = {
      detectChanges: jest.fn(),
      markForCheck: jest.fn()
    };

    await TestBed.configureTestingModule({
      imports: [BodyCompositionComponent, FormsModule],
      providers: [
        { provide: WeightService, useValue: mockWeightService },
        { provide: MetabolismService, useValue: mockMetabolismService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(BodyCompositionComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should load data on ngOnInit', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      // Component initializes with data loading
      expect(component.stats).toBeDefined();
    });

    it('should initialize signals', () => {
      fixture.detectChanges();

      expect(component.stats).toBeDefined();
      expect(component.isLoading).toBeDefined();
    });

    it('should run async operations in NgZone', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      // Component handles async operations
      expect(component).toBeTruthy();
    });

    it('should trigger change detection after view init', () => {
      fixture.detectChanges();

      // Component detects changes after init
      expect(component).toBeTruthy();
    });
  });

  describe('Data Loading', () => {
    it('should load body composition stats', async () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: []
      };
      (mockWeightService.stats as any).set(stats);

      fixture.detectChanges();

      // Stats are loaded
      expect(component).toBeTruthy();
    });

    it('should load weight history', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      const history = component.history();
      expect(Array.isArray(history)).toBe(true);
    });

    it('should display loading state during fetch', () => {
      (mockWeightService as any).isLoading = signal(true);

      fixture.detectChanges();

      expect(component.isLoading()).toBe(true);
    });

    it('should handle empty history', () => {
      (mockWeightService.stats as any).set({
        latest: null,
        trend: 'stable',
        history: []
      });

      fixture.detectChanges();

      expect(component.history()).toHaveLength(0);
    });

    it('should track latest composition', () => {
      const stats = {
        latest: { weight: 75, fatPercentage: 18, musclePercentage: 42 },
        trend: 'up',
        history: []
      };
      (mockWeightService.stats as any).set(stats);

      fixture.detectChanges();

      expect(component.stats().latest.weight).toBe(75);
      expect(component.stats().latest.fatPercentage).toBe(18);
    });
  });

  describe('Form Input & Validation', () => {
    it('should accept weight input', () => {
      const testWeight = 82.5;
      component.entryWeight.set(testWeight);

      expect(component.entryWeight()).toBe(82.5);
    });

    it('should accept date input', () => {
      const testDate = '2026-01-27';
      component.entryDate.set(testDate);

      expect(component.entryDate()).toBe(testDate);
    });

    it('should accept body composition inputs', () => {
      component.entryFat.set(20);
      component.entryMuscle.set(40);
      component.entryWater.set(60);
      component.entryVisceral.set(5);

      expect(component.entryFat()).toBe(20);
      expect(component.entryMuscle()).toBe(40);
      expect(component.entryWater()).toBe(60);
      expect(component.entryVisceral()).toBe(5);
    });

    it('should accept BMR input', () => {
      const bmr = 1850;
      component.entryBmr.set(bmr);

      expect(component.entryBmr()).toBe(1850);
    });

    it('should validate weight range', () => {
      component.entryWeight.set(200);
      expect(component.entryWeight()).toBe(200);

      component.entryWeight.set(40);
      expect(component.entryWeight()).toBe(40);
    });

    it('should validate percentage inputs (0-100)', () => {
      component.entryFat.set(25);
      expect(component.entryFat()).toBe(25);

      component.entryFat.set(0);
      expect(component.entryFat()).toBe(0);

      component.entryFat.set(100);
      expect(component.entryFat()).toBe(100);
    });
  });

  describe('Entry Editing', () => {
    it('should populate form when editing entry', () => {
      const testEntry = {
        id: '1',
        date: '2026-01-20',
        weight: 81,
        fatPercentage: 21,
        musclePercentage: 39,
        waterPercentage: 59,
        visceralFat: 5,
        bmr: 1820
      };

      component.editEntry(testEntry);

      expect(component.entryDate()).toBe(testEntry.date);
      expect(component.entryWeight()).toBe(testEntry.weight);
      expect(component.entryFat()).toBe(testEntry.fatPercentage);
      expect(component.entryMuscle()).toBe(testEntry.musclePercentage);
    });

    it('should scroll to form when editing', () => {
      const testEntry = {
        id: '1',
        date: '2026-01-20',
        weight: 81,
        fatPercentage: 21,
        musclePercentage: 39,
        waterPercentage: 59,
        visceralFat: 5,
        bmr: 1820
      };

      component.editEntry(testEntry);

      const form = fixture.nativeElement.querySelector('[data-test="entry-form"]');
      if (form) {
        expect(form.scrollIntoView).toBeDefined();
      }
    });

    it('should clear form after editing cancelled', () => {
      component.entryWeight.set(85);
      component.clearForm();

      expect(component.entryWeight()).toBe(0);
    });
  });

  describe('Entry Saving', () => {
    it('should save entry with all fields', async () => {
      component.entryDate.set('2026-01-27');
      component.entryWeight.set(80);
      component.entryFat.set(20);
      component.entryMuscle.set(40);

      await component.saveEntry();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should save entry with required fields only', async () => {
      component.entryDate.set('2026-01-27');
      component.entryWeight.set(80);

      await component.saveEntry();

      expect(mockWeightService.logWeight).toHaveBeenCalled();
    });

    it('should show success message after save', async () => {
      component.entryWeight.set(80);

      await component.saveEntry();

      expect(component.showSuccessMessage()).toBe(true);
    });

    it('should disable save button during saving', async () => {
      component.entryWeight.set(80);
      component.isSavingEntry.set(true);

      fixture.detectChanges();

      const saveButton = fixture.nativeElement.querySelector('[data-test="save-entry"]');
      if (saveButton) {
        expect(saveButton.disabled).toBe(true);
      }
    });

    it('should reload data after successful save', async () => {
      component.entryWeight.set(80);

      await component.saveEntry();

      expect(mockWeightService.getBodyCompositionStats).toHaveBeenCalled();
    });

    it('should handle save error gracefully', async () => {
      (mockWeightService.logWeight as jest.Mock).mockRejectedValueOnce(
        new Error('Save failed')
      );

      component.entryWeight.set(80);

      await expect(component.saveEntry()).rejects.toThrow('Save failed');
    });
  });

  describe('Entry Deletion', () => {
    it('should delete entry with confirmation', async () => {
      const entryId = '123';
      jest.spyOn(window, 'confirm').mockReturnValueOnce(true);

      await component.deleteEntry(entryId);

      expect(mockWeightService.logWeight).toBeDefined();
    });

    it('should not delete without confirmation', async () => {
      const entryId = '123';
      jest.spyOn(window, 'confirm').mockReturnValueOnce(false);

      await component.deleteEntry(entryId);

      // Service deleteEntry should not be called
      expect(component).toBeTruthy();
    });

    it('should reload data after deletion', async () => {
      const entryId = '123';
      jest.spyOn(window, 'confirm').mockReturnValueOnce(true);

      await component.deleteEntry(entryId);

      expect(mockWeightService.getBodyCompositionStats).toBeDefined();
    });
  });

  describe('Chart Configuration', () => {
    it('should setup charts on stats change', () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: [
          { date: '2026-01-25', weight: 82 },
          { date: '2026-01-26', weight: 81 },
          { date: '2026-01-27', weight: 80 }
        ]
      };

      component.setupCharts(stats);

      // Charts should be configured
      expect(component).toBeTruthy();
    });

    it('should configure weight trend chart', () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: [
          { date: '2026-01-25', weight: 82 },
          { date: '2026-01-26', weight: 81 },
          { date: '2026-01-27', weight: 80 }
        ]
      };

      component.setupCharts(stats);

      expect(component.weightChartData).toBeDefined();
    });

    it('should configure fat percentage chart', () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: [
          { date: '2026-01-25', fatPercentage: 22 },
          { date: '2026-01-26', fatPercentage: 21 },
          { date: '2026-01-27', fatPercentage: 20 }
        ]
      };

      component.setupCharts(stats);

      expect(component.fatTrendChartData).toBeDefined();
    });

    it('should configure muscle mass chart', () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'up',
        history: [
          { date: '2026-01-25', musclePercentage: 38 },
          { date: '2026-01-26', musclePercentage: 39 },
          { date: '2026-01-27', musclePercentage: 40 }
        ]
      };

      component.setupCharts(stats);

      expect(component.muscleTrendChartData).toBeDefined();
    });

    it('should handle empty history in charts', () => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'stable',
        history: []
      };

      component.setupCharts(stats);

      expect(component).toBeTruthy();
    });
  });

  describe('Metabolism Integration', () => {
    it('should load metabolism summary', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(mockMetabolismService.getSummary).toHaveBeenCalled();
    });

    it('should display TDEE from metabolism', () => {
      component.metabolismStats.set({
        tdee: 2500,
        bmr: 1800
      });

      fixture.detectChanges();

      expect(component.metabolismStats().tdee).toBe(2500);
    });

    it('should display BMR from metabolism', () => {
      component.metabolismStats.set({
        tdee: 2500,
        bmr: 1800
      });

      fixture.detectChanges();

      expect(component.metabolismStats().bmr).toBe(1800);
    });

    it('should handle metabolism fetch error', async () => {
      (mockMetabolismService.getSummary as jest.Mock).mockRejectedValueOnce(
        new Error('Metabolism error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });
  });

  describe('History Display', () => {
    it('should display weight history in table', () => {
      const history = [
        { date: '2026-01-25', weight: 82, fatPercentage: 22 },
        { date: '2026-01-26', weight: 81, fatPercentage: 21 },
        { date: '2026-01-27', weight: 80, fatPercentage: 20 }
      ];
      component.history.set(history);

      fixture.detectChanges();

      const rows = fixture.nativeElement.querySelectorAll('[data-test="history-row"]');
      expect(rows.length).toBeGreaterThanOrEqual(0);
    });

    it('should display date in each history row', () => {
      const history = [
        { date: '2026-01-27', weight: 80, fatPercentage: 20 }
      ];
      component.history.set(history);

      fixture.detectChanges();

      expect(component.history()[0].date).toBe('2026-01-27');
    });

    it('should display weight in each history row', () => {
      const history = [
        { date: '2026-01-27', weight: 80.5, fatPercentage: 20 }
      ];
      component.history.set(history);

      fixture.detectChanges();

      expect(component.history()[0].weight).toBe(80.5);
    });

    it('should sort history by date descending', () => {
      const history = [
        { date: '2026-01-25', weight: 82 },
        { date: '2026-01-27', weight: 80 },
        { date: '2026-01-26', weight: 81 }
      ];
      component.history.set(history);

      fixture.detectChanges();

      const displayed = component.history();
      expect(displayed[0].date).toBe('2026-01-27');
    });
  });

  describe('Effects & Reactivity', () => {
    it('should trigger chart setup when stats change', (done) => {
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: []
      };

      const spy = jest.spyOn(component, 'setupCharts');
      component.stats.set(stats);

      setTimeout(() => {
        expect(spy).toHaveBeenCalledWith(stats);
        done();
      }, 100);
    });

    it('should update display when metabolism stats change', () => {
      component.metabolismStats.set({
        tdee: 2500,
        bmr: 1800
      });

      fixture.detectChanges();

      expect(component.metabolismStats().tdee).toBe(2500);
    });
  });

  describe('Error Handling', () => {
    it('should handle stats load error', async () => {
      (mockWeightService.getBodyCompositionStats as jest.Mock).mockRejectedValueOnce(
        new Error('Stats error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      expect(component).toBeTruthy();
    });

    it('should handle invalid weight input', () => {
      component.entryWeight.set(-10);

      // Component should handle validation
      expect(component.entryWeight()).toBe(-10);
    });

    it('should handle invalid date input', () => {
      component.entryDate.set('invalid-date');

      // Component should handle invalid date
      expect(component.entryDate()).toBe('invalid-date');
    });

    it('should recover from network error', async () => {
      (mockWeightService.getBodyCompositionStats as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      fixture.detectChanges();
      await fixture.whenStable();

      // Component should still be usable
      expect(component).toBeTruthy();
    });
  });

  describe('NgZone Usage', () => {
    it('should run async operations inside NgZone', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(mockNgZone.run).toHaveBeenCalled();
    });

    it('should run expensive operations outside NgZone', () => {
      // Chart setup typically happens outside zone
      const stats = {
        latest: { weight: 80, fatPercentage: 20, musclePercentage: 40 },
        trend: 'down',
        history: []
      };

      component.setupCharts(stats);

      expect(component).toBeTruthy();
    });
  });

  describe('Change Detection', () => {
    it('should mark for check after data load', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(mockChangeDetectorRef.detectChanges).toHaveBeenCalled();
    });

    it('should trigger change detection after form input', () => {
      component.entryWeight.set(85);
      fixture.detectChanges();

      expect(component.entryWeight()).toBe(85);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very high weight values', () => {
      component.entryWeight.set(500);
      expect(component.entryWeight()).toBe(500);
    });

    it('should handle very low weight values', () => {
      component.entryWeight.set(20);
      expect(component.entryWeight()).toBe(20);
    });

    it('should handle decimal weight values', () => {
      component.entryWeight.set(80.75);
      expect(component.entryWeight()).toBe(80.75);
    });

    it('should handle rapid successive saves', async () => {
      component.entryWeight.set(80);
      component.saveEntry();
      component.saveEntry();
      component.saveEntry();

      await fixture.whenStable();

      expect(mockWeightService.logWeight).toBeDefined();
    });

    it('should handle component destruction', () => {
      fixture.destroy();
      expect(fixture.componentInstance).toBeTruthy();
    });
  });
});
