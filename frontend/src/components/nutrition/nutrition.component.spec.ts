import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NutritionComponent } from './nutrition.component';
import { NutritionService } from '../../services/nutrition.service';
import { MetabolismService } from '../../services/metabolism.service';
import { ConfirmationService } from '../../services/confirmation.service';
import { NutritionFactory } from '../../test-utils/factories/nutrition.factory';
import { signal, NO_ERRORS_SCHEMA } from '@angular/core';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, LineController, BarController, DoughnutController, ArcElement } from 'chart.js';

// Register all Chart.js components needed by widgets
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend
);

describe('NutritionComponent', () => {
  let component: NutritionComponent;
  let fixture: ComponentFixture<NutritionComponent>;
  let mockNutritionService: any;
  let mockMetabolismService: any;
  let mockConfirmationService: any;

  beforeEach(async () => {
    mockNutritionService = {
      getLogs: jest.fn().mockResolvedValue({
        logs: NutritionFactory.createLogList(5),
        total_pages: 3,
        total: 15,
        page: 1,
        page_size: 5
      }),
      getStats: jest.fn().mockResolvedValue(NutritionFactory.createStats()),
      deleteLog: jest.fn().mockResolvedValue(undefined)
    };

    mockMetabolismService = {
      stats: signal({
        weight_trend: [],
        tdee: 2500,
        bmr: 1800,
        recommendation: 'Manter'
      } as any),
      fetchSummary: jest.fn().mockResolvedValue({
        tdee: 2500,
        bmr: 1800,
        recommendation: 'Manter'
      })
    };

    mockConfirmationService = {
      confirm: jest.fn().mockResolvedValue(true)
    };

    await TestBed.configureTestingModule({
      imports: [NutritionComponent],
      providers: [
        { provide: NutritionService, useValue: mockNutritionService },
        { provide: MetabolismService, useValue: mockMetabolismService },
        { provide: ConfirmationService, useValue: mockConfirmationService },
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(NutritionComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should load logs and stats on init', async () => {
      fixture.detectChanges();
      await fixture.whenStable();

      expect(mockNutritionService.getLogs).toHaveBeenCalled();
      expect(mockNutritionService.getStats).toHaveBeenCalled();
    });
  });

  describe('Data Loading', () => {
    it('should load nutrition logs', async () => {
      fixture.detectChanges();
      await component.loadLogs();
      expect(component.logs().length).toBe(5);
    });

    it('should hide loading after data loads', async () => {
      fixture.detectChanges();
      await component.loadLogs();
      expect(component.isLoading()).toBe(false);
    });
  });

  describe('Pagination', () => {
    it('should display total pages', async () => {
      fixture.detectChanges();
      await component.loadLogs();
      expect(component.totalPages()).toBe(3);
    });

    it('should go to next page', async () => {
      fixture.detectChanges();
      await component.loadLogs();
      
      mockNutritionService.getLogs.mockClear();
      component.currentPage.set(1);
      component.totalPages.set(3);

      await component.nextPage();

      expect(mockNutritionService.getLogs).toHaveBeenCalled();
      expect(component.currentPage()).toBe(2);
    });
  });

  describe('Macro Calculations', () => {
    it('should calculate macro percentages', () => {
      expect(component.getMacroPercentage(200, 'protein', 1000)).toBe('80%');
    });
  });

  describe('Log Deletion', () => {
    it('should delete log with confirmation', async () => {
      fixture.detectChanges();
      const log = NutritionFactory.createBreakfast();
      mockConfirmationService.confirm.mockResolvedValueOnce(true);

      await component.deleteLog(new Event('click'), log);

      expect(mockNutritionService.deleteLog).toHaveBeenCalledWith(log.id);
    });

    it('should reload data after deletion', async () => {
      fixture.detectChanges();
      const log = NutritionFactory.createBreakfast();
      mockConfirmationService.confirm.mockResolvedValueOnce(true);
      mockNutritionService.getLogs.mockClear();

      await component.deleteLog(new Event('click'), log);

      expect(mockNutritionService.getLogs).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle load logs error', async () => {
      fixture.detectChanges();
      mockNutritionService.getLogs.mockRejectedValueOnce(new Error('Network error'));
      
      await component.loadLogs();

      expect(component.isLoading()).toBe(false);
    });

    it('should handle load stats error', async () => {
      fixture.detectChanges();
      mockNutritionService.getStats.mockRejectedValueOnce(new Error('Stats error'));
      
      await component.loadStats();

      // Should not crash and stats should stay as they were (null or prev value)
      expect(component.stats()).toBeDefined(); 
    });
  });
});
