import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TelegramService } from './telegram.service';
import { environment } from '../environment';

describe('TelegramService', () => {
  let service: TelegramService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TelegramService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(TelegramService);
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

  describe('generateCode()', () => {
    it('should generate linking code', async () => {
      const promise = service.generateCode();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/generate-code')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});

      req.flush({
        code: 'TELEGRAM_CODE_12345',
        expires_in_seconds: 600
      });

      const result = await promise;

      expect(result.code).toBe('TELEGRAM_CODE_12345');
      expect(result.expires_in_seconds).toBe(600);
    });

    it('should handle code generation error', async () => {
      const promise = service.generateCode();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/generate-code')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle unauthorized error', async () => {
      const promise = service.generateCode();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/generate-code')
      );
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const promise = service.generateCode();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/generate-code')
      );
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should return code with different expiry times', async () => {
      const expiryTimes = [300, 600, 900, 1800];

      for (const expiry of expiryTimes) {
        const promise = service.generateCode();

        const req = httpMock.expectOne(req =>
          req.url.includes('/telegram/generate-code')
        );
        req.flush({
          code: 'CODE_' + expiry,
          expires_in_seconds: expiry
        });

        const result = await promise;

        expect(result.expires_in_seconds).toBe(expiry);
      }
    });
  });

  describe('getStatus()', () => {
    it('should get Telegram linked status', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      expect(req.request.method).toBe('GET');

      req.flush({
        linked: true,
        telegram_username: '@myusername',
        linked_at: '2026-01-25T10:00:00Z'
      });

      const result = await promise;

      expect(result.linked).toBe(true);
      expect(result.telegram_username).toBe('@myusername');
      expect(result.linked_at).toBe('2026-01-25T10:00:00Z');
    });

    it('should handle not linked status', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );

      req.flush({
        linked: false
      });

      const result = await promise;

      expect(result.linked).toBe(false);
      expect(result.telegram_username).toBeUndefined();
      expect(result.linked_at).toBeUndefined();
    });

    it('should handle status error', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle unauthorized error', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const promise = service.getStatus();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('unlink()', () => {
    it('should unlink Telegram account', async () => {
      const promise = service.unlink();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({});

      req.flush({ success: true });

      await promise;
      expect(true).toBe(true);
    });

    it('should handle unlink error', async () => {
      const promise = service.unlink();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle not linked error', async () => {
      const promise = service.unlink();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      req.flush('Not linked', { status: 400, statusText: 'Bad Request' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle unauthorized error', async () => {
      const promise = service.unlink();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle network error', async () => {
      const promise = service.unlink();

      const req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      req.error(new ProgressEvent('error'));

      try {
        await promise;
        fail('Should have thrown error');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Integration Flow', () => {
    it('should complete full Telegram linking flow', async () => {
      // 1. Generate linking code
      let promise = service.generateCode();
      let req = httpMock.expectOne(req =>
        req.url.includes('/telegram/generate-code')
      );
      req.flush({
        code: 'LINK_CODE_123',
        expires_in_seconds: 600
      });
      let code = await promise;
      expect(code.code).toBe('LINK_CODE_123');

      // 2. Check status (should be not linked yet)
      promise = service.getStatus();
      req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush({ linked: false });
      let status = await promise;
      expect(status.linked).toBe(false);

      // 3. After user scans code, check status again (should be linked)
      promise = service.getStatus();
      req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush({
        linked: true,
        telegram_username: '@user123',
        linked_at: new Date().toISOString()
      });
      status = await promise;
      expect(status.linked).toBe(true);
      expect(status.telegram_username).toBe('@user123');
    });

    it('should complete full Telegram unlinking flow', async () => {
      // 1. Check current status (linked)
      let promise = service.getStatus();
      let req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush({
        linked: true,
        telegram_username: '@user123',
        linked_at: '2026-01-25T10:00:00Z'
      });
      let status = await promise;
      expect(status.linked).toBe(true);

      // 2. Unlink
      promise = service.unlink();
      req = httpMock.expectOne(req =>
        req.url.includes('/telegram/unlink')
      );
      req.flush({ success: true });
      await promise;

      // 3. Check status again (should be not linked)
      promise = service.getStatus();
      req = httpMock.expectOne(req =>
        req.url.includes('/telegram/status')
      );
      req.flush({ linked: false });
      status = await promise;
      expect(status.linked).toBe(false);
    });
  });
});
