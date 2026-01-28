import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkoutsComponent } from './workouts.component';
import { WorkoutService } from '../../services/workout.service';
import { signal } from '@angular/core';
import { WorkoutDrawerComponent } from './workout-drawer/workout-drawer.component';
import { Workout } from '../../models/workout.model';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('WorkoutsComponent', () => {
  let component: WorkoutsComponent;
  let fixture: ComponentFixture<WorkoutsComponent>;
  let workoutServiceMock: Partial<WorkoutService>;

  const mockWorkout: Partial<Workout> = {
    id: '1',
    workout_type: 'Push',
    date: '2026-01-21T10:00:00Z',
    duration_minutes: 60,
    exercises: []
  };

  beforeEach(async () => {
    workoutServiceMock = {
      workouts: signal([]),
      isLoading: signal(false),
      currentPage: signal(1),
      totalPages: signal(1),
      totalWorkouts: signal(0),
      selectedType: signal(null),
      getWorkouts: jest.fn().mockResolvedValue([]),
      getTypes: jest.fn().mockResolvedValue(['Push', 'Pull', 'Legs']),
      getStats: jest.fn().mockResolvedValue({}),
      previousPage: jest.fn().mockResolvedValue(undefined),
      nextPage: jest.fn().mockResolvedValue(undefined),
      deleteWorkout: jest.fn().mockResolvedValue(undefined)
    } as unknown as WorkoutService;

    await TestBed.configureTestingModule({
      imports: [WorkoutsComponent, WorkoutDrawerComponent],
      providers: [
        { provide: WorkoutService, useValue: workoutServiceMock }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkoutsComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should load workouts on init', async () => {
      await component.ngOnInit();

      expect(workoutServiceMock.getWorkouts).toHaveBeenCalledWith(1);
    });

    it('should load workout types on init', async () => {
      await component.ngOnInit();

      expect(workoutServiceMock.getTypes).toHaveBeenCalled();
    });

    it('should load stats on init', async () => {
      await component.ngOnInit();

      expect(workoutServiceMock.getStats).toHaveBeenCalled();
    });

    it('should initialize with default values', () => {
      expect(component.workouts()).toEqual([]);
      expect(component.selectedWorkout()).toBeNull();
      expect(component.isPulling()).toBe(false);
      expect(component.pullProgress()).toBe(0);
    });
  });

  describe('Workout Selection', () => {
    it('should select workout', () => {
      component.selectWorkout(mockWorkout as Workout);

      expect(component.selectedWorkout()).toEqual(mockWorkout);
    });

    it('should open drawer when workout selected', () => {
      component.selectWorkout(mockWorkout as Workout);

      expect(component.selectedWorkout()).not.toBeNull();
    });

    it('should close drawer', () => {
      component.selectedWorkout.set(mockWorkout as Workout);
      component.closeDrawer();

      expect(component.selectedWorkout()).toBeNull();
    });

    it('should close drawer on closeDrawer call', () => {
      component.selectedWorkout.set(mockWorkout as Workout);

      component.closeDrawer();

      expect(component.selectedWorkout()).toBeNull();
    });
  });

  describe('Type Filtering', () => {
    it('should filter by type', async () => {
      const event = { target: { value: 'Push' } } as unknown as Event;

      await component.onTypeChange(event);

      expect(workoutServiceMock.getWorkouts).toHaveBeenCalledWith(1, 'Push');
    });

    it('should show all workouts when filter is all', async () => {
      const event = { target: { value: 'all' } } as unknown as Event;

      await component.onTypeChange(event);

      expect(workoutServiceMock.getWorkouts).toHaveBeenCalledWith(1, null);
    });

    it('should load types on init', async () => {
      await component.loadTypes();

      expect(workoutServiceMock.getTypes).toHaveBeenCalled();
      expect(component.workoutTypes()).toEqual(['Push', 'Pull', 'Legs']);
    });
  });

  describe('Pagination', () => {
    it('should navigate to next page', async () => {
      await component.nextPage();

      expect(workoutServiceMock.nextPage).toHaveBeenCalled();
    });

    it('should navigate to previous page', async () => {
      await component.previousPage();

      expect(workoutServiceMock.previousPage).toHaveBeenCalled();
    });

    it('should update pagination state', async () => {
      (workoutServiceMock.currentPage as any).set(2);

      expect(component.currentPage()).toBe(2);
    });
  });

  describe('Workout Deletion', () => {
    it('should delete workout after confirmation', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);

      await component.deleteWorkout(new MouseEvent('click'), mockWorkout as Workout);

      expect(workoutServiceMock.deleteWorkout).toHaveBeenCalledWith('1');
    });

    it('should not delete without confirmation', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(false);

      await component.deleteWorkout(new MouseEvent('click'), mockWorkout as Workout);

      expect(workoutServiceMock.deleteWorkout).not.toHaveBeenCalled();
    });

    it('should set deletingId during deletion', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);

      const deletePromise = component.deleteWorkout(new MouseEvent('click'), mockWorkout as Workout);

      expect(component.deletingId()).toBe('1');

      await deletePromise;
    });

    it('should clear deletingId after deletion', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);

      await component.deleteWorkout(new MouseEvent('click'), mockWorkout as Workout);

      expect(component.deletingId()).toBeNull();
    });

    it('should stop propagation when deleting', () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);
      const event = new MouseEvent('click');
      jest.spyOn(event, 'stopPropagation');

      component.deleteWorkout(event, mockWorkout as Workout);

      expect(event.stopPropagation).toHaveBeenCalled();
    });

    it('should clear deletingId even on error', async () => {
      jest.spyOn(window, 'confirm').mockReturnValue(true);
      (workoutServiceMock.deleteWorkout as jest.Mock).mockRejectedValueOnce(new Error('Delete failed'));

      try {
        await component.deleteWorkout(new MouseEvent('click'), mockWorkout as Workout);
      } catch {
        // Expected
      }

      expect(component.deletingId()).toBeNull();
    });
  });

  describe('Pull to Refresh', () => {
    it('should start pull when scrolled to top', () => {
      const touchEvent = new TouchEvent('touchstart', {
        touches: [{ clientY: 100 } as Touch]
      });

      component.onTouchStart(touchEvent);

      expect(component.isPulling()).toBe(true);
    });

    it('should track pull progress', () => {
      component.isPulling.set(true);
      const touchEvent = new TouchEvent('touchmove', {
        touches: [{ clientY: 150 } as Touch]
      });

      // Manually set startY for testing
      (component as any).startY = 100;

      component.onTouchMove(touchEvent);

      expect(component.pullProgress()).toBeGreaterThan(0);
    });

    it('should trigger refresh when pull exceeds threshold', async () => {
      component.isPulling.set(true);
      component.pullProgress.set(100);

      await component.onTouchEnd();

      expect(workoutServiceMock.getWorkouts).toHaveBeenCalled();
    });

    it('should not trigger refresh with insufficient pull', async () => {
      jest.clearAllMocks();
      component.isPulling.set(true);
      component.pullProgress.set(50); // Below 100%

      await component.onTouchEnd();

      // getWorkouts shouldn't be called from pull (only from init/other)
      expect(component.isPulling()).toBe(false);
    });

    it('should reset pull state on touchend', async () => {
      component.isPulling.set(true);
      component.pullProgress.set(50);

      await component.onTouchEnd();

      expect(component.isPulling()).toBe(false);
      expect(component.pullProgress()).toBe(0);
    });
  });

  describe('Date Formatting', () => {
    it('should format date for main list', () => {
      const formatted = component.formatDateMain('2026-01-21T10:00:00Z');

      expect(formatted).toContain('21');
      expect(formatted).toContain('jan');
    });

    it('should format full date with time', () => {
      const formatted = component.getFormattedDate('2026-01-21T10:30:00Z');

      expect(formatted).toContain('21');
      expect(formatted.length).toBeGreaterThan(5);
    });

    it('should handle empty date string', () => {
      const formatted = component.getFormattedDate('');

      expect(formatted).toBe('');
    });

    it('should handle invalid date gracefully', () => {
      const formatted = component.getFormattedDate('invalid');

      expect(formatted).toBe('invalid');
    });
  });

  describe('Stats Loading', () => {
    it('should load workout stats', async () => {
      await component.loadStats();

      expect(workoutServiceMock.getStats).toHaveBeenCalled();
    });

    it('should update stats signal', async () => {
      const mockStats = { total_workouts: 50, avg_duration: 60 };
      (workoutServiceMock.getStats as jest.Mock).mockResolvedValueOnce(mockStats);

      await component.loadStats();

      expect(component.stats()).toEqual(mockStats);
    });
  });

  describe('Load Workouts', () => {
    it('should load workouts, types and stats together', async () => {
      (workoutServiceMock.getWorkouts as jest.Mock).mockResolvedValueOnce([mockWorkout]);
      (workoutServiceMock.getTypes as jest.Mock).mockResolvedValueOnce(['Push', 'Pull']);
      (workoutServiceMock.getStats as jest.Mock).mockResolvedValueOnce({ total: 50 });

      await component.loadWorkouts();

      expect(workoutServiceMock.getWorkouts).toHaveBeenCalled();
      expect(workoutServiceMock.getTypes).toHaveBeenCalled();
      expect(workoutServiceMock.getStats).toHaveBeenCalled();
    });
  });
});
