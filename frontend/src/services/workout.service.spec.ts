import { TestBed } from '@angular/core/testing';
import { WorkoutService } from './workout.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';
import { WorkoutListResponse } from '../models/workout.model';

describe('WorkoutService', () => {
  let service: WorkoutService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        WorkoutService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(WorkoutService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch workouts and update signals', async () => {
    const mockResponse: WorkoutListResponse = {
      workouts: [
        {
          id: '1',
          user_email: 'test@test.com',
          date: new Date().toISOString(),
          workout_type: 'Push',
          exercises: [],
          duration_minutes: 60
        }
      ],
      total: 10,
      page: 1,
      page_size: 10,
      total_pages: 1
    };

    const promise = service.getWorkouts(1);

    const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);

    await promise;

    expect(service.workouts().length).toBe(1);
    expect(service.totalWorkouts()).toBe(10);
    expect(service.isLoading()).toBe(false);
  });

  it('should fetch workouts with type filter', async () => {
    const mockWorkouts: WorkoutListResponse = {
        workouts: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
    };

    const promise = service.getWorkouts(1, 'Push');

    const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10&workout_type=Push`);
    req.flush(mockWorkouts);

    await promise;
    expect(service.selectedType()).toBe('Push');
  });

  it('should fetch workout types', async () => {
    const mockTypes = ['Push', 'Pull', 'Legs'];
    const promise = service.getTypes();

    const req = httpMock.expectOne(`${environment.apiUrl}/workout/types`);
    req.flush(mockTypes);

    const types = await promise;
    expect(types).toEqual(mockTypes);
  });

  describe('Error Handling', () => {
    it('should handle error in getWorkouts', async () => {
      const promise = service.getWorkouts(1);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      req.error(new ErrorEvent('Network error'));

      const result = await promise;

      expect(result).toEqual([]);
      expect(service.isLoading()).toBe(false);
    });

    it('should handle error in getTypes', async () => {
      const promise = service.getTypes();

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/types`);
      req.error(new ErrorEvent('Network error'));

      const result = await promise;

      expect(result).toEqual([]);
    });

    it('should set isLoading to false after error', async () => {
      expect(service.isLoading()).toBe(false);

      const promise = service.getWorkouts(1);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      req.error(new ErrorEvent('Error'));

      await promise;

      expect(service.isLoading()).toBe(false);
    });
  });

  describe('Pagination', () => {
    it('should move to next page', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [{ id: '2', user_email: 'test@test.com', date: new Date().toISOString(), workout_type: 'Pull', exercises: [], duration_minutes: 60 }],
        total: 25,
        page: 2,
        page_size: 10,
        total_pages: 3
      };

      service.currentPage.set(1);
      service.totalPages.set(3);

      const promise = service.nextPage();

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=2&page_size=10`);
      req.flush(mockResponse);

      await promise;

      expect(service.currentPage()).toBe(2);
    });

    it('should not move to next page if at last page', async () => {
      service.currentPage.set(3);
      service.totalPages.set(3);

      await service.nextPage();

      expect(service.currentPage()).toBe(3);
    });

    it('should move to previous page', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 25,
        page: 1,
        page_size: 10,
        total_pages: 3
      };

      service.currentPage.set(2);
      service.totalPages.set(3);

      const promise = service.previousPage();

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      req.flush(mockResponse);

      await promise;

      expect(service.currentPage()).toBe(1);
    });

    it('should not move to previous page if at first page', async () => {
      service.currentPage.set(1);
      service.totalPages.set(3);

      await service.previousPage();

      expect(service.currentPage()).toBe(1);
    });

    it('should handle custom page size', async () => {
      service.pageSize.set(20);

      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 50,
        page: 1,
        page_size: 20,
        total_pages: 3
      };

      const promise = service.getWorkouts(1);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=20`);
      req.flush(mockResponse);

      await promise;
    });
  });

  describe('Type Filtering', () => {
    it('should update selectedType when type changes', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      };

      service.selectedType.set(null);

      const promise = service.getWorkouts(1, 'Legs');

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10&workout_type=Legs`);
      req.flush(mockResponse);

      await promise;

      expect(service.selectedType()).toBe('Legs');
    });

    it('should not update selectedType if same type', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      };

      service.selectedType.set('Push');

      const promise = service.getWorkouts(1, 'Push');

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10&workout_type=Push`);
      req.flush(mockResponse);

      await promise;

      expect(service.selectedType()).toBe('Push');
    });

    it('should clear type filter with null', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      };

      service.selectedType.set('Push');

      const promise = service.getWorkouts(1, null);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      expect(req.request.params.has('workout_type')).toBe(false);
      req.flush(mockResponse);

      await promise;

      expect(service.selectedType()).toBeNull();
    });
  });


  describe('Workout Stats', () => {
    it('should fetch workout stats', async () => {
      const mockStats = {
        total_workouts: 50,
        total_volume: 50000,
        avg_duration: 45
      };

      const promise = service.getStats();

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/stats`);
      req.flush(mockStats);

      const stats = await promise;

      expect(stats).toEqual(mockStats);
    });

    it('should handle error in getStats', async () => {
      const promise = service.getStats();

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/stats`);
      req.error(new ErrorEvent('Server error'));

      try {
        await promise;
      } catch (e) {
        expect(e).toBeDefined();
      }
    });
  });

  describe('Signal Updates', () => {
    it('should update all signals when loading workouts', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [
          { id: '1', user_email: 'test@test.com', date: new Date().toISOString(), workout_type: 'Push', exercises: [], duration_minutes: 60 },
          { id: '2', user_email: 'test@test.com', date: new Date().toISOString(), workout_type: 'Pull', exercises: [], duration_minutes: 55 }
        ],
        total: 25,
        page: 2,
        page_size: 10,
        total_pages: 3
      };

      const promise = service.getWorkouts(2);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=2&page_size=10`);
      req.flush(mockResponse);

      await promise;

      expect(service.workouts().length).toBe(2);
      expect(service.currentPage()).toBe(2);
      expect(service.totalPages()).toBe(3);
      expect(service.totalWorkouts()).toBe(25);
      expect(service.isLoading()).toBe(false);
    });

    it('should set isLoading signal to true during fetch', () => {
      expect(service.isLoading()).toBe(false);

      const promise = service.getWorkouts(1);

      expect(service.isLoading()).toBe(true);

      const req = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      };
      req.flush(mockResponse);

      return promise.then(() => {
        expect(service.isLoading()).toBe(false);
      });
    });
  });

  describe('Multiple Requests', () => {
    it('should handle rapid pagination', async () => {
      const mockResponse: WorkoutListResponse = {
        workouts: [],
        total: 50,
        page: 1,
        page_size: 10,
        total_pages: 5
      };

      service.totalPages.set(5);
      service.currentPage.set(1);

      const promise1 = service.getWorkouts(1);
      const promise2 = service.getWorkouts(2);

      const req1 = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=1&page_size=10`);
      const req2 = httpMock.expectOne(`${environment.apiUrl}/workout/list?page=2&page_size=10`);

      req1.flush({ ...mockResponse, page: 1 });
      req2.flush({ ...mockResponse, page: 2 });

      await Promise.all([promise1, promise2]);

      expect(service.currentPage()).toBe(2);
    });
  });
});
