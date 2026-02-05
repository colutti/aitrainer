import { TestBed } from '@angular/core/testing';
import { NutritionService } from './nutrition.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';

describe('NutritionService', () => {
  let service: NutritionService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        NutritionService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(NutritionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getLogs', () => {
    it('should call GET /nutrition/list with pagination params', async () => {
      const mockResponse = {
        logs: [{ calories: 2000, protein_grams: 150 }],
        total: 1,
        page: 1,
        page_size: 10
      };

      const promise = service.getLogs(1, 10);
      const req = httpMock.expectOne(
        `${environment.apiUrl}/nutrition/list?page=1&page_size=10`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);

      const res = await promise;
      expect(res).toEqual(mockResponse);
    });

    it('should include days param when provided', async () => {
      const promise = service.getLogs(1, 10, 7);

      const req = httpMock.expectOne(
        `${environment.apiUrl}/nutrition/list?page=1&page_size=10&days=7`
      );
      expect(req.request.method).toBe('GET');
      req.flush({ logs: [], total: 0, page: 1, page_size: 10 });

      await promise;
    });
  });

  describe('getStats', () => {
    it('should call GET /nutrition/stats and update signal', async () => {
      const mockStats = {
        daily_target: 2000,
        current_macros: {
          calories: 1800,
          protein: 120,
          carbs: 200,
          fat: 60
        }
      } as any;

      const promise = service.getStats();
      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/stats`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStats);

      const res = await promise;
      expect(res).toEqual(mockStats);

      // Verify signal was updated
      expect(service.stats()).toEqual(mockStats);
    });

    it('should handle error gracefully', async () => {
      const promise = service.getStats();
      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/stats`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      try {
        await promise;
        fail('Should have failed');
      } catch (err) {
        expect(err).toBeTruthy();
      }
    });
  });

  describe('getTodayLog', () => {
    it('should call GET /nutrition/today', async () => {
      const mockTodayLog = {
        date: '2026-01-13',
        calories: 1500,
        protein_grams: 100
      } as any;

      const promise = service.getTodayLog();
      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/today`);
      expect(req.request.method).toBe('GET');
      req.flush(mockTodayLog);

      const res = await promise;
      expect(res).toEqual(mockTodayLog);
    });
  });
});
