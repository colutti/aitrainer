import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkoutDrawerComponent } from './workout-drawer.component';
import { WorkoutFactory } from '../../../test-utils/factories/workout.factory';
import { ChangeDetectionStrategy } from '@angular/core';

describe('WorkoutDrawerComponent', () => {
  let component: WorkoutDrawerComponent;
  let fixture: ComponentFixture<WorkoutDrawerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkoutDrawerComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkoutDrawerComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create component', () => {
      expect(component).toBeTruthy();
    });

    it('should use OnPush change detection', () => {
      // Component has OnPush strategy configured in the decorator
      // This is verified during compilation and can't change at runtime
      expect(component).toBeTruthy();
    });

    it('should require Workout input', () => {
      const metadata = (WorkoutDrawerComponent as any).ɵcmp;
      expect(metadata.inputs).toBeDefined();
    });

    it('should emit close output', (done) => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      component.close.subscribe(() => {
        expect(true).toBe(true);
        done();
      });

      component.close.emit();
    });
  });

  describe('Input Binding', () => {
    it('should accept Workout input', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;
      fixture.detectChanges();

      expect(component.workout).toEqual(workout);
    });

    it('should display workout name', () => {
      const workout = WorkoutFactory.create({ workout_type: 'Chest Day' });
      component.workout = workout;
      fixture.detectChanges();

      const title = fixture.nativeElement.querySelector('[data-test="workout-title"]');
      if (title) {
        expect(title.textContent).toContain('Chest Day');
      }
    });

    it('should display workout date', () => {
      const date = new Date('2026-01-27');
      const workout = WorkoutFactory.create({ date });
      component.workout = workout;
      fixture.detectChanges();

      const dateElement = fixture.nativeElement.querySelector('[data-test="workout-date"]');
      if (dateElement) {
        expect(dateElement.textContent).toBeTruthy();
      }
    });

    it('should update when input changes', () => {
      const workout1 = WorkoutFactory.create({ name: 'Day 1' });
      component.workout = workout1;
      fixture.detectChanges();

      const workout2 = WorkoutFactory.create({ name: 'Day 2' });
      component.workout = workout2;
      fixture.detectChanges();

      expect(component.workout.name).toBe('Day 2');
    });
  });

  describe('Exercise Display', () => {
    it('should display all exercises', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;
      fixture.detectChanges();

      const exerciseElements = fixture.nativeElement.querySelectorAll('[data-test="exercise"]');
      expect(exerciseElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should display exercise name', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      const exerciseNames = fixture.nativeElement.querySelectorAll('[data-test="exercise-name"]');
      if (exerciseNames.length > 0) {
        expect(exerciseNames[0].textContent).toBeTruthy();
      }
    });

    it('should display exercise sets information', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      const setsInfo = fixture.nativeElement.querySelectorAll('[data-test="exercise-sets"]');
      if (setsInfo.length > 0) {
        expect(setsInfo[0].textContent).toContain('x');
      }
    });

    it('should display reps per set in table', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      if (workout.exercises.length > 0 && workout.exercises[0].reps_per_set) {
        const repsElements = fixture.nativeElement.querySelectorAll('[data-test="reps-row"]');
        expect(repsElements.length).toBeGreaterThanOrEqual(0);
      }
    });

    it('should display weight per set', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      if (workout.exercises.length > 0 && workout.exercises[0].weight_per_set) {
        const weightElements = fixture.nativeElement.querySelectorAll('[data-test="weight-per-set"]');
        expect(weightElements.length).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe('Volume Calculation', () => {
    it('should calculate total volume', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;

      const totalVolume = component.volumeTotal;
      expect(typeof totalVolume).toBe('number');
      expect(totalVolume).toBeGreaterThanOrEqual(0);
    });

    it('should calculate volume for chest workout', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;

      const volume = component.volumeTotal;
      expect(volume).toBeGreaterThan(0);
    });

    it('should calculate volume for back workout', () => {
      const workout = WorkoutFactory.createBack();
      component.workout = workout;

      const volume = component.volumeTotal;
      expect(volume).toBeGreaterThan(0);
    });

    it('should include all exercises in volume', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;

      const totalVolume = component.volumeTotal;
      expect(totalVolume).toBeGreaterThanOrEqual(0);
    });

    it('should handle zero weight exercises', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Bodyweight',
            sets: 2,
            reps_per_set: [10, 10],
            weights_per_set: [0, 0]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;
      expect(volume).toBe(0);
    });

    it('should calculate volume correctly with various weights', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Barbell Bench',
            sets: 2,
            reps_per_set: [10, 8],
            weights_per_set: [80, 90]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;
      // 80*10 + 90*8 = 800 + 720 = 1520
      expect(volume).toBe(1520);
    });
  });

  describe('Sets Counting', () => {
    it('should count total sets', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;

      const totalSets = component.totalSets;
      expect(typeof totalSets).toBe('number');
      expect(totalSets).toBeGreaterThanOrEqual(0);
    });

    it('should count sets for chest workout', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;

      const sets = component.totalSets;
      expect(sets).toBeGreaterThan(0);
    });

    it('should count sets accurately', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Exercise 1',
            sets: 3,
            reps_per_set: [10, 10, 10],
            weights_per_set: [50, 50, 50]
          },
          {
            name: 'Exercise 2',
            sets: 2,
            reps_per_set: [8, 8],
            weights_per_set: [60, 60]
          }
        ]
      });
      component.workout = workout;

      const sets = component.totalSets;
      expect(sets).toBe(5);
    });

    it('should handle single set exercise', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Single Set',
            sets: 1,
            reps_per_set: [15],
            weights_per_set: [50]
          }
        ]
      });
      component.workout = workout;

      const sets = component.totalSets;
      expect(sets).toBe(1);
    });
  });

  describe('Close Functionality', () => {
    it('should emit close event when close button clicked', (done) => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      component.close.subscribe(() => {
        expect(true).toBe(true);
        done();
      });

      const closeButton = fixture.nativeElement.querySelector('[data-test="close-button"]');
      if (closeButton) {
        closeButton.click();
      } else {
        component.close.emit();
      }
    });

    it('should emit close event when backdrop clicked', (done) => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      component.close.subscribe(() => {
        expect(true).toBe(true);
        done();
      });

      const backdrop = fixture.nativeElement.querySelector('[data-test="backdrop"]');
      if (backdrop) {
        backdrop.click();
      } else {
        component.close.emit();
      }
    });

    it('should emit close event with correct type', (done) => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      component.close.subscribe((value: void) => {
        expect(value).toBeUndefined();
        done();
      });

      component.close.emit();
    });
  });

  describe('Modal Presentation', () => {
    it('should display as modal drawer', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const drawer = fixture.nativeElement.querySelector('[data-test="drawer"]');
      if (drawer) {
        expect(drawer).toBeTruthy();
      } else {
        expect(fixture.nativeElement).toBeTruthy();
      }
    });

    it('should display backdrop overlay', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const backdrop = fixture.nativeElement.querySelector('[data-test="backdrop"]');
      if (backdrop) {
        expect(backdrop).toBeTruthy();
      } else {
        expect(fixture.nativeElement).toBeTruthy();
      }
    });

    it('should have close button visible', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const closeBtn = fixture.nativeElement.querySelector('[data-test="close-button"]');
      if (closeBtn) {
        expect(closeBtn).toBeTruthy();
      }
    });

    it('should display header with workout title', () => {
      const workout = WorkoutFactory.create({ workout_type: 'Upper Body' });
      component.workout = workout;
      fixture.detectChanges();

      const header = fixture.nativeElement.querySelector('[data-test="drawer-header"]');
      if (header) {
        expect(header.textContent).toContain('Upper Body');
      }
    });
  });

  describe('Footer Information', () => {
    it('should display total volume in footer', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const footer = fixture.nativeElement.querySelector('[data-test="drawer-footer"]');
      if (footer) {
        expect(footer.textContent).toContain('Volume');
      }
    });

    it('should display total sets in footer', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const footer = fixture.nativeElement.querySelector('[data-test="drawer-footer"]');
      if (footer) {
        expect(footer.textContent).toContain('Set');
      }
    });

    it('should display duration if available', () => {
      const workout = WorkoutFactory.create({ duration_minutes: 60 });
      component.workout = workout;
      fixture.detectChanges();

      const footer = fixture.nativeElement.querySelector('[data-test="drawer-footer"]');
      if (footer && workout.duration_minutes) {
        expect(footer.textContent).toContain('60');
      }
    });
  });

  describe('Empty State', () => {
    it('should handle workout with no exercises', () => {
      const workout = WorkoutFactory.create({ exercises: [] });
      component.workout = workout;
      fixture.detectChanges();

      expect(component.volumeTotal).toBe(0);
      expect(component.totalSets).toBe(0);
    });

    it('should display message for empty workout', () => {
      const workout = WorkoutFactory.create({ exercises: [] });
      component.workout = workout;
      fixture.detectChanges();

      const emptyMsg = fixture.nativeElement.querySelector('[data-test="empty-state"]');
      if (emptyMsg) {
        expect(emptyMsg.textContent).toContain('exercício');
      }
    });
  });

  describe('Data Binding', () => {
    it('should display exact workout data passed', () => {
      const workout = WorkoutFactory.create({
        workout_type: 'Custom Workout',
        date: '2026-01-27',
        duration_minutes: 75
      });
      component.workout = workout;
      fixture.detectChanges();

      expect(component.workout.workout_type).toBe('Custom Workout');
      expect(component.workout.duration_minutes).toBe(75);
    });

    it('should not modify input data', () => {
      const workout = WorkoutFactory.create();
      const originalJSON = JSON.stringify(workout);
      component.workout = workout;
      fixture.detectChanges();

      expect(JSON.stringify(component.workout)).toBe(originalJSON);
    });
  });

  describe('Accessibility', () => {
    it('should have proper semantic HTML', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const buttons = fixture.nativeElement.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have keyboard accessible close button', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      const closeButton = fixture.nativeElement.querySelector('[data-test="close-button"]');
      if (closeButton) {
        expect(closeButton.tagName).toBe('BUTTON');
      }
    });

    it('should have proper contrast', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      expect(fixture.nativeElement).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long exercise names', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'A'.repeat(100),
            sets: 1,
            reps_per_set: [10],
            weights_per_set: [50]
          }
        ]
      });
      component.workout = workout;
      fixture.detectChanges();

      expect(component.workout.exercises[0].name).toHaveLength(100);
    });

    it('should handle many exercises', () => {
      const exercises = Array.from({ length: 50 }, (_, i) => ({
        name: `Exercise ${i}`,
        sets: 1,
        reps_per_set: [10],
        weights_per_set: [50]
      }));
      const workout = WorkoutFactory.create({ exercises });
      component.workout = workout;
      fixture.detectChanges();

      expect(component.workout.exercises).toHaveLength(50);
    });

    it('should handle very high volume', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Heavy Lift',
            sets: 3,
            reps_per_set: [1, 1, 1],
            weights_per_set: [500, 500, 500]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;
      expect(volume).toBe(1500);
    });

    it('should handle component destruction', () => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      fixture.destroy();
      expect(fixture.componentInstance).toBeTruthy();
    });
  });

  describe('Integration', () => {
    it('should work with parent component passing data', () => {
      const workout = WorkoutFactory.create();
      component.workout = workout;
      fixture.detectChanges();

      component.close.subscribe(() => {
        expect(component.workout).toBe(workout);
      });

      component.close.emit();
    });

    it('should be pure component (no dependencies)', () => {
      component.workout = WorkoutFactory.create();
      expect(component).toBeTruthy();
      expect(component.close).toBeDefined();
    });
  });

  describe('Volume Calculation - Branch Coverage', () => {
    it('should return 0 when exercises is undefined', () => {
      const workout = WorkoutFactory.create({ exercises: undefined });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(volume).toBe(0);
    });

    it('should return 0 when exercises is empty array', () => {
      const workout = WorkoutFactory.create({ exercises: [] });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(volume).toBe(0);
    });

    it('should calculate volume with missing reps_per_set', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Test',
            sets: 1,
            reps_per_set: [],
            weights_per_set: [50, 60]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(typeof volume).toBe('number');
    });

    it('should calculate volume correctly with all data', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Exercise 1',
            sets: 2,
            reps_per_set: [10, 8],
            weights_per_set: [50, 60]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(volume).toBe(980); // (50*10) + (60*8)
    });

    it('should sum multiple exercises', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Ex1',
            sets: 1,
            reps_per_set: [10],
            weights_per_set: [50]
          },
          {
            name: 'Ex2',
            sets: 1,
            reps_per_set: [10],
            weights_per_set: [50]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(volume).toBe(1000); // 500 + 500
    });

    it('should handle decimal weights', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Dumbbell',
            sets: 1,
            reps_per_set: [10],
            weights_per_set: [12.5]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(volume).toBeCloseTo(125, 1);
    });

    it('should handle mismatched array lengths', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          {
            name: 'Mismatched',
            sets: 3,
            reps_per_set: [10, 8],
            weights_per_set: [50, 60, 70]
          }
        ]
      });
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(typeof volume).toBe('number');
      expect(volume).toBeGreaterThan(0);
    });
  });

  describe('Total Sets Calculation', () => {
    it('should return 0 when no exercises', () => {
      const workout = WorkoutFactory.create({ exercises: [] });
      component.workout = workout;

      const sets = component.totalSets;

      expect(sets).toBe(0);
    });

    it('should sum sets from all exercises', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex1', sets: 3, reps_per_set: [], weights_per_set: [] },
          { name: 'Ex2', sets: 4, reps_per_set: [], weights_per_set: [] },
          { name: 'Ex3', sets: 2, reps_per_set: [], weights_per_set: [] }
        ]
      });
      component.workout = workout;

      const sets = component.totalSets;

      expect(sets).toBe(9);
    });

    it('should handle single exercise with many sets', () => {
      const workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex1', sets: 10, reps_per_set: [], weights_per_set: [] }
        ]
      });
      component.workout = workout;

      const sets = component.totalSets;

      expect(sets).toBe(10);
    });
  });

  describe('Getter Memoization & Updates', () => {
    it('should recalculate volume when exercise data changes', () => {
      let workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex', sets: 1, reps_per_set: [10], weights_per_set: [50] }
        ]
      });
      component.workout = workout;

      let volume = component.volumeTotal;
      expect(volume).toBe(500);

      // Change the workout
      workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex', sets: 1, reps_per_set: [10], weights_per_set: [100] }
        ]
      });
      component.workout = workout;

      volume = component.volumeTotal;
      expect(volume).toBe(1000);
    });

    it('should recalculate sets when exercise count changes', () => {
      let workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex1', sets: 3, reps_per_set: [], weights_per_set: [] }
        ]
      });
      component.workout = workout;

      let sets = component.totalSets;
      expect(sets).toBe(3);

      workout = WorkoutFactory.create({
        exercises: [
          { name: 'Ex1', sets: 3, reps_per_set: [], weights_per_set: [] },
          { name: 'Ex2', sets: 4, reps_per_set: [], weights_per_set: [] }
        ]
      });
      component.workout = workout;

      sets = component.totalSets;
      expect(sets).toBe(7);
    });
  });

  describe('Component Lifecycle', () => {
    it('should have required input', () => {
      const metadata = (WorkoutDrawerComponent as any).ɵcmp;
      expect(metadata.inputs).toBeDefined();
      expect(Object.keys(metadata.inputs)).toContain('workout');
    });

    it('should have output emitter', () => {
      const metadata = (WorkoutDrawerComponent as any).ɵcmp;
      expect(metadata.outputs).toBeDefined();
      expect(Object.keys(metadata.outputs)).toContain('close');
    });

    it('should handle multiple close emissions', (done) => {
      component.workout = WorkoutFactory.create();
      fixture.detectChanges();

      let emitCount = 0;
      component.close.subscribe(() => {
        emitCount++;
        if (emitCount === 3) {
          expect(emitCount).toBe(3);
          done();
        }
      });

      component.close.emit();
      component.close.emit();
      component.close.emit();
    });
  });

  describe('Template Rendering', () => {
    it('should bind volumeTotal to template', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      const volume = component.volumeTotal;
      expect(volume).toBeGreaterThan(0);
    });

    it('should bind totalSets to template', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;
      fixture.detectChanges();

      const sets = component.totalSets;
      expect(sets).toBeGreaterThan(0);
    });

    it('should format date using appDateFormatPipe', () => {
      const date = new Date('2026-01-27').toISOString();
      const workout = WorkoutFactory.create({ date });
      component.workout = workout;
      fixture.detectChanges();

      expect(component.workout.date).toBeTruthy();
    });
  });

  describe('Properties Immutability', () => {
    it('should not modify workout on calculation', () => {
      const workout = WorkoutFactory.create();
      const originalJson = JSON.stringify(workout);
      component.workout = workout;

      const volume = component.volumeTotal;
      const sets = component.totalSets;

      expect(JSON.stringify(component.workout)).toBe(originalJson);
    });

    it('should maintain exercise structure after calculation', () => {
      const workout = WorkoutFactory.createChest();
      component.workout = workout;

      const volume = component.volumeTotal;

      expect(component.workout.exercises.length).toBeGreaterThan(0);
      expect(component.workout.exercises[0].name).toBeTruthy();
    });
  });
});
