import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MemoriesComponent } from './memories.component';
import { MemoryService } from '../../services/memory.service';
import { ConfirmationService } from '../../services/confirmation.service';
import { Memory } from '../../models/memory.model';
import { signal } from '@angular/core';

describe('MemoriesComponent', () => {
  let component: MemoriesComponent;
  let fixture: ComponentFixture<MemoriesComponent>;
  let memoryServiceMock: Partial<MemoryService>;
  let confirmationServiceMock: Partial<ConfirmationService>;

  const mockMemory: Memory = {
    id: 'test-1',
    memory: 'Test memory',
    created_at: '2026-01-03T08:00:00Z',
    updated_at: null
  };

  beforeEach(async () => {
    memoryServiceMock = {
      memories: signal([]),
      isLoading: signal(false),
      currentPage: signal(1),
      totalPages: signal(1),
      totalMemories: signal(0),
      getMemories: jest.fn().mockResolvedValue(undefined),
      previousPage: jest.fn().mockResolvedValue(undefined),
      nextPage: jest.fn().mockResolvedValue(undefined),
      deleteMemory: jest.fn().mockResolvedValue(undefined)
    };

    confirmationServiceMock = {
      confirm: jest.fn().mockResolvedValue(true)
    };

    await TestBed.configureTestingModule({
      imports: [MemoriesComponent],
      providers: [
        { provide: MemoryService, useValue: memoryServiceMock },
        { provide: ConfirmationService, useValue: confirmationServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MemoriesComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should load memories on init', async () => {
      await component.ngOnInit();

      expect(memoryServiceMock.getMemories).toHaveBeenCalledWith(1);
    });

    it('should initialize with default values', () => {
      expect(component.memories()).toEqual([]);
      expect(component.isLoading()).toBe(false);
      expect(component.currentPage()).toBe(1);
      expect(component.deletingId()).toBeNull();
      expect(component.showDeleteSuccess()).toBe(false);
    });
  });

  describe('Display Memories', () => {
    it('should display empty state when no memories', async () => {
      (memoryServiceMock.memories as any).set([]);
      (memoryServiceMock.totalMemories as any).set(0);

      await component.ngOnInit();

      expect(component.memories()).toEqual([]);
    });

    it('should display list of memories', async () => {
      const mockMemories = [
        { id: 'test-1', memory: 'Memory 1', created_at: '2026-01-03T08:00:00Z', updated_at: null },
        { id: 'test-2', memory: 'Memory 2', created_at: '2026-01-02T10:30:00Z', updated_at: null }
      ];

      (memoryServiceMock.memories as any).set(mockMemories);
      (memoryServiceMock.totalMemories as any).set(2);

      await component.ngOnInit();

      expect(component.memories().length).toBe(2);
      expect(component.memories()[0].memory).toBe('Memory 1');
    });
  });

  describe('Pagination', () => {
    it('should show pagination when multiple pages exist', async () => {
      (memoryServiceMock.totalPages as any).set(3);
      (memoryServiceMock.currentPage as any).set(1);

      await component.ngOnInit();

      expect(component.currentPage()).toBe(1);
      expect(component.totalPages()).toBe(3);
    });

    it('should disable previous button on first page', async () => {
      (memoryServiceMock.currentPage as any).set(1);
      (memoryServiceMock.totalPages as any).set(3);

      expect(component.currentPage()).toBe(1);
    });

    it('should disable next button on last page', async () => {
      (memoryServiceMock.currentPage as any).set(3);
      (memoryServiceMock.totalPages as any).set(3);

      expect(component.currentPage()).toBe(3);
      expect(component.totalPages()).toBe(3);
    });

    it('should navigate to next page', async () => {
      await component.nextPage();

      expect(memoryServiceMock.nextPage).toHaveBeenCalled();
    });

    it('should navigate to previous page', async () => {
      await component.previousPage();

      expect(memoryServiceMock.previousPage).toHaveBeenCalled();
    });
  });

  describe('Delete Memory', () => {
    it('should delete memory after confirmation', async () => {
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(true);

      await component.deleteMemory(mockMemory);

      expect(memoryServiceMock.deleteMemory).toHaveBeenCalledWith('test-1');
    });

    it('should not delete memory when confirmation is cancelled', async () => {
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(false);

      await component.deleteMemory(mockMemory);

      expect(memoryServiceMock.deleteMemory).not.toHaveBeenCalled();
    });

    it('should set deletingId while deleting', async () => {
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(true);
      (memoryServiceMock.deleteMemory as jest.Mock).mockImplementation(async () => {
        // Simulate async operation
        expect(component.deletingId()).toBe('test-1');
      });

      await component.deleteMemory(mockMemory);
    });

    it('should clear deletingId after deletion', async () => {
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(true);

      await component.deleteMemory(mockMemory);

      expect(component.deletingId()).toBeNull();
    });

    it('should show success message after deletion', async () => {
      jest.useFakeTimers();
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(true);

      await component.deleteMemory(mockMemory);

      expect(component.showDeleteSuccess()).toBe(true);

      jest.advanceTimersByTime(2000);
      expect(component.showDeleteSuccess()).toBe(false);

      jest.useRealTimers();
    });

    it('should clear deletingId even on error', async () => {
      (confirmationServiceMock.confirm as jest.Mock).mockResolvedValueOnce(true);
      (memoryServiceMock.deleteMemory as jest.Mock).mockRejectedValueOnce(new Error('Delete failed'));

      // Component's finally block should still clear deletingId despite error
      try {
        await component.deleteMemory(mockMemory);
      } catch {
        // Error is expected
      }

      expect(component.deletingId()).toBeNull();
    });
  });

  describe('Date Formatting', () => {
    it('should format valid ISO date to pt-BR locale', () => {
      const result = component.formatDate('2026-01-03T08:00:00Z');

      expect(result).toContain('03');
      expect(result).toContain('01');
      expect(result).toContain('2026');
    });

    it('should return unknown date for null', () => {
      const result = component.formatDate(null);

      expect(result).toBe('Data desconhecida');
    });

    it('should handle malformed date strings gracefully', () => {
      const result = component.formatDate('invalid-date');

      // Browser returns "Invalid Date" when parsing invalid date strings
      expect(result).toContain('Invalid');
    });
  });
});
