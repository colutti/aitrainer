import { TestBed } from '@angular/core/testing';
import { PaginationService } from './pagination.service';

describe('PaginationService', () => {
  let service: PaginationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PaginationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start at page 1', () => {
    expect(service.getCurrentPage()()).toBe(1);
  });

  it('should go to next page', () => {
    service.setTotalPages(5);
    service.nextPage();
    expect(service.getCurrentPage()()).toBe(2);
  });

  it('should not go beyond total pages', () => {
    service.setTotalPages(3);
    service.nextPage();
    service.nextPage();
    service.nextPage();
    expect(service.getCurrentPage()()).toBe(3);
  });

  it('should go to previous page', () => {
    service.setTotalPages(5);
    service.goToPage(3);
    service.prevPage();
    expect(service.getCurrentPage()()).toBe(2);
  });

  it('should reset to page 1', () => {
    service.goToPage(5);
    service.reset();
    expect(service.getCurrentPage()()).toBe(1);
  });

  it('should get current state', () => {
    service.setTotalPages(10);
    service.setPageSize(20);
    service.goToPage(5);
    const state = service.getState();
    expect(state.currentPage).toBe(5);
    expect(state.totalPages).toBe(10);
    expect(state.pageSize).toBe(20);
  });
});
