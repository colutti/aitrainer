import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkoutsComponent } from './workouts.component';
import { WorkoutService } from '../../services/workout.service';
import { signal } from '@angular/core';
import { WorkoutDrawerComponent } from './workout-drawer/workout-drawer.component';
import { Workout } from '../../models/workout.model';

describe('WorkoutsComponent', () => {
  let component: WorkoutsComponent;
  let fixture: ComponentFixture<WorkoutsComponent>;
  let workoutServiceMock: Partial<WorkoutService>;

  beforeEach(async () => {
    workoutServiceMock = {
      workouts: signal([]),
      isLoading: signal(false),
      currentPage: signal(1),
      totalPages: signal(1),
      totalWorkouts: signal(0),
      selectedType: signal(null),
      getWorkouts: jest.fn().mockReturnValue(Promise.resolve([])),
      getTypes: jest.fn().mockReturnValue(Promise.resolve([])),
      previousPage: jest.fn(),
      nextPage: jest.fn()
    } as unknown as WorkoutService;

    await TestBed.configureTestingModule({
      imports: [WorkoutsComponent, WorkoutDrawerComponent],
      providers: [
        { provide: WorkoutService, useValue: workoutServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkoutsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load workouts and types on init', () => {
    expect(workoutServiceMock.getWorkouts).toHaveBeenCalledWith(1);
    expect(workoutServiceMock.getTypes).toHaveBeenCalled();
  });

  it('should open drawer when workout selected', () => {
    const mockWorkout = { id: '1', workout_type: 'Push' } as unknown as Workout;
    component.selectWorkout(mockWorkout);
    expect(component.selectedWorkout()).toEqual(mockWorkout);
  });

  it('should close drawer', () => {
    component.selectedWorkout.set({} as unknown as Workout);
    component.closeDrawer();
    expect(component.selectedWorkout()).toBeNull();
  });

  it('should filter by type', () => {
    // Simulate select change event
    const event = { target: { value: 'Push' } } as unknown as Event;
    component.onTypeChange(event);
    expect(workoutServiceMock.getWorkouts).toHaveBeenCalledWith(1, 'Push');
  });
});
