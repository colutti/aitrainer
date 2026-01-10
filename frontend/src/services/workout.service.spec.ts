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
});
