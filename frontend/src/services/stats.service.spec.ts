import { TestBed } from '@angular/core/testing';
import { StatsService } from './stats.service';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../environment';
import { WorkoutStats } from '../models/stats.model';

describe('StatsService', () => {
  let service: StatsService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        StatsService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(StatsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch stats and update signal', async () => {
    const mockStats: WorkoutStats = {
      user_email: 'test@test.com',
      total_workouts: 10,
      total_duration_minutes: 600,
      total_volume_kg: 50000,
      favorite_exercise: 'Bench Press',
      current_streak_weeks: 5,
      weekly_frequency: 3,
      weekly_volume_per_category: { 'Chest': 1000 },
      recent_prs: [],
      last_workout: null
    };

    const promise = service.fetchStats();

    const req = httpMock.expectOne(`${environment.apiUrl}/workout/stats`);
    expect(req.request.method).toBe('GET');
    req.flush(mockStats);

    await promise;

    expect(service.stats()).toEqual(mockStats);
    expect(service.isLoading()).toBe(false);
  });

  it('should handle error when fetching stats', async () => {
    const promise = service.fetchStats();

    const req = httpMock.expectOne(`${environment.apiUrl}/workout/stats`);
    req.flush('Error', { status: 500, statusText: 'Server Error' });

    await promise;

    expect(service.stats()).toBeNull();
    expect(service.isLoading()).toBe(false);
  });
});
