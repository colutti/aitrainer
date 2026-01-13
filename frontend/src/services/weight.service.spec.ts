import { TestBed } from '@angular/core/testing';
import { WeightService } from './weight.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';

describe('WeightService', () => {
  let service: WeightService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        WeightService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(WeightService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('logWeight', () => {
    it('should call POST /weight with correct payload', async () => {
      const promise = service.logWeight(75.5);

      const req = httpMock.expectOne(`${environment.apiUrl}/weight`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body.weight_kg).toBe(75.5);
      expect(req.request.body.source).toBe('manual');
      req.flush({ message: 'ok', id: '123' });

      await promise;
      expect(service.lastSaved()).toBe(true);
    });

    it('should include composition data in payload', async () => {
      const promise = service.logWeight(80, { body_fat_pct: 22, muscle_mass_pct: 55 });

      const req = httpMock.expectOne(`${environment.apiUrl}/weight`);
      expect(req.request.body.weight_kg).toBe(80);
      expect(req.request.body.body_fat_pct).toBe(22);
      expect(req.request.body.muscle_mass_pct).toBe(55);
      req.flush({ message: 'ok' });

      await promise;
    });

    it('should throw error on API failure', async () => {
      const promise = service.logWeight(75);

      const req = httpMock.expectOne(`${environment.apiUrl}/weight`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      await expect(promise).rejects.toBeTruthy();
    });
  });

  describe('getHistory', () => {
    it('should call GET /weight with limit parameter', async () => {
      const mockHistory = [
        { weight_kg: 75, date: '2026-01-10' },
        { weight_kg: 76, date: '2026-01-09' }
      ];

      const promise = service.getHistory();

      const req = httpMock.expectOne(`${environment.apiUrl}/weight?limit=30`);
      expect(req.request.method).toBe('GET');
      req.flush(mockHistory);

      const result = await promise;
      expect(result.length).toBe(2);
      expect(result[0].weight_kg).toBe(75);
    });

    it('should return empty array on error', async () => {
      const promise = service.getHistory();

      const req = httpMock.expectOne(`${environment.apiUrl}/weight?limit=30`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      const result = await promise;
      expect(result).toEqual([]);
    });
  });

  describe('getBodyCompositionStats', () => {
    it('should call GET /weight/stats', async () => {
      const mockStats = { 
        latest: { weight_kg: 75 }, 
        weight_trend: [] 
      };

      const promise = service.getBodyCompositionStats();

      const req = httpMock.expectOne(`${environment.apiUrl}/weight/stats`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStats);

      const result = await promise;
      expect(result).toEqual(mockStats);
    });

    it('should return null on error', async () => {
      const promise = service.getBodyCompositionStats();

      const req = httpMock.expectOne(`${environment.apiUrl}/weight/stats`);
      req.flush('Error', { status: 500, statusText: 'Server Error' });

      const result = await promise;
      expect(result).toBeNull();
    });
  });

  describe('deleteWeight', () => {
    it('should call DELETE /weight/:date', async () => {
      const promise = service.deleteWeight('2026-01-10');

      const req = httpMock.expectOne(`${environment.apiUrl}/weight/2026-01-10`);
      expect(req.request.method).toBe('DELETE');
      req.flush({ message: 'ok', deleted: true });

      await promise;
    });

    it('should throw error on API failure', async () => {
      const promise = service.deleteWeight('2026-01-10');

      const req = httpMock.expectOne(`${environment.apiUrl}/weight/2026-01-10`);
      req.flush('Error', { status: 404, statusText: 'Not Found' });

      await expect(promise).rejects.toBeTruthy();
    });
  });
});
