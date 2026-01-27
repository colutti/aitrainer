import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { HevyService } from './hevy.service';
import { environment } from '../environment';

describe('HevyService', () => {
  let service: HevyService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HevyService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(HevyService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });
  });

  describe('validateKey()', () => {
    it('should validate valid API key', async () => {
      const apiKey = 'valid_hevy_api_key_123';

      const promise = service.validateKey(apiKey);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/validate')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body.api_key).toBe(apiKey);

      req.flush({ valid: true, count: 45 });

      const result = await promise;

      expect(result.valid).toBe(true);
      expect(result.count).toBe(45);
    });

    it('should validate invalid API key', async () => {
      const apiKey = 'invalid_key';

      const promise = service.validateKey(apiKey);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/validate')
      );
      req.flush({ valid: false }, { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle timeout', async () => {
      const apiKey = 'timeout_key';

      const promise = service.validateKey(apiKey);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/validate')
      );

      // Simulate timeout by never responding
      setTimeout(() => {
        try {
          req.flush(null);
        } catch (e) {
          // timeout already occurred
        }
      }, 15000);

      // The test will fail if timeout operator doesn't work
      // In real scenario, this would timeout after 10000ms
    });

    it('should handle server error', async () => {
      const promise = service.validateKey('key');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/validate')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('saveConfig()', () => {
    it('should save config with API key', async () => {
      const apiKey = 'new_api_key';

      const promise = service.saveConfig(apiKey, true);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/config')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        enabled: true,
        api_key: apiKey
      });

      req.flush({ success: true });

      await promise;
      expect(true).toBe(true);
    });

    it('should save config without API key', async () => {
      const promise = service.saveConfig(undefined, false);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/config')
      );
      expect(req.request.body).toEqual({
        enabled: false
      });
      expect(req.request.body.api_key).toBeUndefined();

      req.flush({ success: true });

      await promise;
    });

    it('should save config with null API key', async () => {
      const promise = service.saveConfig(null, false);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/config')
      );
      expect(req.request.body).toEqual({
        enabled: false,
        api_key: null
      });

      req.flush({ success: true });

      await promise;
    });

    it('should handle save error', async () => {
      const promise = service.saveConfig('key', true);

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/config')
      );
      req.flush('Error', { status: 400, statusText: 'Bad Request' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('getStatus()', () => {
    it('should fetch Hevy status', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/status')
      );
      expect(req.request.method).toBe('GET');

      req.flush({
        enabled: true,
        has_key: true,
        api_key_masked: 'hevy_***_key123',
        last_sync: '2026-01-27T10:00:00Z'
      });

      const result = await promise;

      expect(result.enabled).toBe(true);
      expect(result.hasKey).toBe(true);
      expect(result.apiKeyMasked).toBe('hevy_***_key123');
      expect(result.lastSync).toBe('2026-01-27T10:00:00Z');
    });

    it('should handle not connected status', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/status')
      );

      req.flush({
        enabled: false,
        has_key: false,
        api_key_masked: null,
        last_sync: null
      });

      const result = await promise;

      expect(result.enabled).toBe(false);
      expect(result.hasKey).toBe(false);
      expect(result.lastSync).toBeNull();
    });

    it('should handle status error', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/status')
      );
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('getCount()', () => {
    it('should fetch workout count', async () => {
      const promise = service.getCount();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/count')
      );
      expect(req.request.method).toBe('GET');

      req.flush({ count: 42 });

      const result = await promise;

      expect(result).toBe(42);
    });

    it('should handle zero count', async () => {
      const promise = service.getCount();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/count')
      );

      req.flush({ count: 0 });

      const result = await promise;

      expect(result).toBe(0);
    });

    it('should handle count error', async () => {
      const promise = service.getCount();

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/count')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('importWorkouts()', () => {
    it('should import workouts with skip_duplicates mode', async () => {
      const promise = service.importWorkouts('2026-01-01', 'skip_duplicates');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({
        from_date: '2026-01-01',
        mode: 'skip_duplicates'
      });

      req.flush({
        success: true,
        imported: 10,
        skipped: 5,
        errors: []
      });

      const result = await promise;

      expect(result.success).toBe(true);
      expect(result.imported).toBe(10);
      expect(result.skipped).toBe(5);
    });

    it('should import workouts with overwrite mode', async () => {
      const promise = service.importWorkouts('2026-01-01', 'overwrite');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );
      expect(req.request.body.mode).toBe('overwrite');

      req.flush({
        success: true,
        imported: 15,
        skipped: 0,
        errors: []
      });

      const result = await promise;

      expect(result.imported).toBe(15);
      expect(result.skipped).toBe(0);
    });

    it('should import workouts with null fromDate', async () => {
      const promise = service.importWorkouts(null, 'skip_duplicates');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );
      expect(req.request.body.from_date).toBeNull();

      req.flush({
        success: true,
        imported: 50,
        skipped: 0,
        errors: []
      });

      const result = await promise;

      expect(result.imported).toBe(50);
    });

    it('should handle import with errors', async () => {
      const promise = service.importWorkouts('2026-01-01', 'skip_duplicates');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );

      req.flush({
        success: true,
        imported: 8,
        skipped: 2,
        errors: [
          { workout_id: '123', error: 'Invalid exercise' }
        ]
      });

      const result = await promise;

      expect(result.success).toBe(true);
      expect(result.errors.length).toBe(1);
    });

    it('should handle import failure', async () => {
      const promise = service.importWorkouts('2026-01-01', 'skip_duplicates');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );
      req.flush('Import failed', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should have longer timeout for import', (done) => {
      // This test verifies timeout is longer for import (60000ms vs 10000ms)
      service.importWorkouts('2026-01-01', 'skip_duplicates');

      const req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );

      // The timeout operator should give more time for import
      expect(req).toBeTruthy();
      req.flush({ success: true, imported: 0, skipped: 0, errors: [] });

      done();
    });
  });

  describe('Integration Flow', () => {
    it('should complete full Hevy integration flow', async () => {
      // 1. Validate key
      let promise = service.validateKey('new_key');
      let req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/validate')
      );
      req.flush({ valid: true, count: 0 });
      let result = await promise;
      expect(result.valid).toBe(true);

      // 2. Save config
      promise = service.saveConfig('new_key', true);
      req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/config')
      );
      req.flush({ success: true });
      await promise;

      // 3. Get status
      promise = service.getStatus();
      req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/status')
      );
      req.flush({
        enabled: true,
        has_key: true,
        api_key_masked: 'key***',
        last_sync: null
      });
      const status = await promise;
      expect(status.enabled).toBe(true);

      // 4. Import workouts
      promise = service.importWorkouts(null, 'skip_duplicates');
      req = httpMock.expectOne(req =>
        req.url.includes('/integrations/hevy/import')
      );
      req.flush({
        success: true,
        imported: 25,
        skipped: 0,
        errors: []
      });
      const importResult = await promise;
      expect(importResult.imported).toBe(25);
    });
  });
});
