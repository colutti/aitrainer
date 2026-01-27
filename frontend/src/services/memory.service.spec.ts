import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { MemoryService } from './memory.service';
import { environment } from '../environment';

describe('MemoryService', () => {
  let service: MemoryService;
  let httpMock: HttpTestingController;

  const mockMemoryListResponse = {
    memories: [
      { id: '1', text: 'Memory 1', timestamp: '2026-01-27T10:00:00Z' },
      { id: '2', text: 'Memory 2', timestamp: '2026-01-27T11:00:00Z' }
    ],
    page: 1,
    page_size: 10,
    total: 15,
    total_pages: 2
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MemoryService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(MemoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Initialization', () => {
    it('should be created', () => {
      expect(service).toBeTruthy();
    });

    it('should initialize with default values', () => {
      expect(service.memories()).toEqual([]);
      expect(service.isLoading()).toBe(false);
      expect(service.currentPage()).toBe(1);
      expect(service.pageSize()).toBe(10);
      expect(service.totalPages()).toBe(0);
      expect(service.totalMemories()).toBe(0);
    });
  });

  describe('getMemories()', () => {
    it('should fetch memories successfully', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('page')).toBe('1');
      expect(req.request.params.get('page_size')).toBe('10');

      req.flush(mockMemoryListResponse);

      const result = await promise;

      expect(result).toEqual(mockMemoryListResponse.memories);
      expect(service.memories()).toEqual(mockMemoryListResponse.memories);
      expect(service.currentPage()).toBe(1);
      expect(service.totalPages()).toBe(2);
      expect(service.totalMemories()).toBe(15);
    });

    it('should fetch specific page', async () => {
      const promise = service.getMemories(2);

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      expect(req.request.params.get('page')).toBe('2');

      req.flush({
        ...mockMemoryListResponse,
        page: 2
      });

      await promise;

      expect(service.currentPage()).toBe(2);
    });

    it('should set isLoading during request', async () => {
      const loadingDuring = {
        start: false,
        end: false
      };

      // Store loading state when request starts
      const promise = service.getMemories();
      loadingDuring.start = service.isLoading();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush(mockMemoryListResponse);

      await promise;

      loadingDuring.end = service.isLoading();

      expect(loadingDuring.start).toBe(true);
      expect(loadingDuring.end).toBe(false);
    });

    it('should handle API error', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      const result = await promise;

      expect(result).toEqual([]);
      expect(service.memories()).toEqual([]);
      expect(service.isLoading()).toBe(false);
    });

    it('should respect custom page size', async () => {
      service.pageSize.set(5);

      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      expect(req.request.params.get('page_size')).toBe('5');

      req.flush(mockMemoryListResponse);

      await promise;
    });

    it('should handle empty response', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({
        memories: [],
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0
      });

      const result = await promise;

      expect(result).toEqual([]);
      expect(service.totalMemories()).toBe(0);
    });
  });

  describe('nextPage()', () => {
    beforeEach(async () => {
      service.currentPage.set(1);
      service.totalPages.set(3);

      const promise = service.getMemories();
      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush(mockMemoryListResponse);
      await promise;
    });

    it('should navigate to next page', async () => {
      const promise = service.nextPage();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      expect(req.request.params.get('page')).toBe('2');

      req.flush({
        ...mockMemoryListResponse,
        page: 2
      });

      await promise;

      expect(service.currentPage()).toBe(2);
    });

    it('should not go beyond last page', async () => {
      service.currentPage.set(3);
      service.totalPages.set(3);

      await service.nextPage();

      httpMock.expectNone(req => req.url.includes('/memory/list'));
      expect(service.currentPage()).toBe(3);
    });

    it('should increment page correctly when navigating multiple times', async () => {
      // Page 1 -> 2
      let promise = service.nextPage();
      let req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({ ...mockMemoryListResponse, page: 2 });
      await promise;
      expect(service.currentPage()).toBe(2);

      // Page 2 -> 3
      promise = service.nextPage();
      req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({ ...mockMemoryListResponse, page: 3 });
      await promise;
      expect(service.currentPage()).toBe(3);
    });
  });

  describe('previousPage()', () => {
    beforeEach(async () => {
      service.currentPage.set(2);
      service.totalPages.set(3);

      const promise = service.getMemories(2);
      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({
        ...mockMemoryListResponse,
        page: 2
      });
      await promise;
    });

    it('should navigate to previous page', async () => {
      const promise = service.previousPage();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      expect(req.request.params.get('page')).toBe('1');

      req.flush({
        ...mockMemoryListResponse,
        page: 1
      });

      await promise;

      expect(service.currentPage()).toBe(1);
    });

    it('should not go before first page', async () => {
      service.currentPage.set(1);

      await service.previousPage();

      httpMock.expectNone(req => req.url.includes('/memory/list'));
      expect(service.currentPage()).toBe(1);
    });

    it('should decrement page correctly when navigating multiple times', async () => {
      service.currentPage.set(3);

      // Page 3 -> 2
      let promise = service.previousPage();
      let req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({ ...mockMemoryListResponse, page: 2 });
      await promise;
      expect(service.currentPage()).toBe(2);

      // Page 2 -> 1
      promise = service.previousPage();
      req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({ ...mockMemoryListResponse, page: 1 });
      await promise;
      expect(service.currentPage()).toBe(1);
    });
  });

  describe('Error Handling', () => {
    it('should handle network error', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.error(new ProgressEvent('error'));

      const result = await promise;

      expect(result).toEqual([]);
      expect(service.isLoading()).toBe(false);
    });

    it('should handle 404 not found', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });

      const result = await promise;

      expect(result).toEqual([]);
    });

    it('should handle 500 server error', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });

      const result = await promise;

      expect(result).toEqual([]);
    });
  });

  describe('Pagination Boundaries', () => {
    it('should handle single page of memories', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({
        memories: [mockMemoryListResponse.memories[0]],
        page: 1,
        page_size: 10,
        total: 1,
        total_pages: 1
      });

      await promise;

      expect(service.totalPages()).toBe(1);
      expect(service.currentPage()).toBe(1);

      // Should not allow next page
      await service.nextPage();
      httpMock.expectNone(req => req.url.includes('/memory/list'));
    });

    it('should handle many pages', async () => {
      const promise = service.getMemories();

      const req = httpMock.expectOne(req => req.url.includes('/memory/list'));
      req.flush({
        ...mockMemoryListResponse,
        total_pages: 100,
        total: 1000
      });

      await promise;

      expect(service.totalPages()).toBe(100);
      expect(service.totalMemories()).toBe(1000);
    });
  });
});
