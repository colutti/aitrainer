import { TestBed } from '@angular/core/testing';
import { MetabolismService } from './metabolism.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';
import { MetabolismResponse } from '../models/metabolism.model';

describe('MetabolismService', () => {
  let service: MetabolismService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MetabolismService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(MetabolismService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have initial null stats', () => {
    expect(service.stats()).toBeNull();
    expect(service.isLoading()).toBe(false);
  });

  describe('fetchSummary', () => {
    it('should call GET /metabolism/summary with weeks param', async () => {
      const mockResponse = {
        tdee: 2500,
        daily_target: 2500,
        confidence: 'high',
        avg_calories: 2400,
        weight_change_per_week: -0.5,
        goal_weekly_rate: -0.5,
        logs_count: 21,
        start_weight: 80,
        end_weight: 78.5
      };

      const promise = service.fetchSummary(3);

      // Should show loading
      expect(service.isLoading()).toBe(true);

      const req = httpMock.expectOne(`${environment.apiUrl}/metabolism/summary?weeks=3`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);

      await promise;

      expect(service.stats()).toEqual(mockResponse);
      expect(service.isLoading()).toBe(false);
    });

    it('should use default weeks=3 when not specified', async () => {
      const promise = service.fetchSummary();

      const req = httpMock.expectOne(`${environment.apiUrl}/metabolism/summary?weeks=3`);
      req.flush({ tdee: 2000, confidence: 'low' } as MetabolismResponse);

      await promise;
    });

    it('should set stats to null on error', async () => {
      // First set some stats
      service.stats.set({ tdee: 1000 } as unknown as MetabolismResponse);

      const promise = service.fetchSummary();

      const req = httpMock.expectOne(`${environment.apiUrl}/metabolism/summary?weeks=3`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      await promise;

      expect(service.stats()).toBeNull();
      expect(service.isLoading()).toBe(false);
    });

    it('should always set isLoading to false after request', async () => {
      const promise = service.fetchSummary();

      expect(service.isLoading()).toBe(true);

      const req = httpMock.expectOne(`${environment.apiUrl}/metabolism/summary?weeks=3`);
      req.flush({ tdee: 2200 });

      await promise;

      expect(service.isLoading()).toBe(false);
    });
  });
});
