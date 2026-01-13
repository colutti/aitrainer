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
    it('should call GET /nutrition/list with pagination params', () => {
      const mockResponse = {
        logs: [{ calories: 2000, protein_grams: 150 }],
        total: 1,
        page: 1,
        page_size: 10
      };

      service.getLogs(1, 10).subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(
        `${environment.apiUrl}/nutrition/list?page=1&page_size=10`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should include days param when provided', () => {
      service.getLogs(1, 10, 7).subscribe();

      const req = httpMock.expectOne(
        `${environment.apiUrl}/nutrition/list?page=1&page_size=10&days=7`
      );
      expect(req.request.method).toBe('GET');
      req.flush({ logs: [], total: 0, page: 1, page_size: 10 });
    });
  });

  describe('getStats', () => {
    it('should call GET /nutrition/stats and update signal', () => {
      const mockStats = {
        daily_target: 2000,
        current_macros: {
          calories: 1800,
          protein: 120,
          carbs: 200,
          fat: 60
        }
      };

      service.getStats().subscribe(res => {
        expect(res).toEqual(mockStats);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/stats`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStats);

      // Verify signal was updated
      expect(service.stats()).toEqual(mockStats);
    });

    it('should handle error gracefully', () => {
      service.getStats().subscribe({
        error: err => expect(err).toBeTruthy()
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/stats`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });
    });
  });

  describe('getTodayLog', () => {
    it('should call GET /nutrition/today', () => {
      const mockTodayLog = {
        date: '2026-01-13',
        calories: 1500,
        protein_grams: 100
      };

      service.getTodayLog().subscribe(res => {
        expect(res).toEqual(mockTodayLog);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/nutrition/today`);
      expect(req.request.method).toBe('GET');
      req.flush(mockTodayLog);
    });
  });
});
