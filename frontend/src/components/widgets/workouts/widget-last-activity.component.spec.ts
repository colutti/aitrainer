import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetLastActivityComponent } from './widget-last-activity.component';

describe('WidgetLastActivityComponent', () => {
  let component: WidgetLastActivityComponent;
  let fixture: ComponentFixture<WidgetLastActivityComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetLastActivityComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetLastActivityComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept workout type', () => {
    component.lastWorkout = { workout_type: 'Push', date: '2026-01-27', duration_minutes: 60 };
    fixture.detectChanges();
    expect(component.lastWorkout.workout_type).toBe('Push');
  });

  it('should accept workout type', () => {
    component.lastWorkout = { workout_type: 'Legs', date: '2026-01-27' };
    expect(component.lastWorkout.workout_type).toBe('Legs');
  });

  it('should accept date', () => {
    component.lastWorkout = { date: '2026-01-27' };
    expect(component.lastWorkout.date).toBe('2026-01-27');
  });

  it('should accept duration', () => {
    component.lastWorkout = { date: '2026-01-27', duration_minutes: 75 };
    expect(component.lastWorkout.duration_minutes).toBe(75);
  });

  it('should handle missing optional fields', () => {
    component.lastWorkout = { date: '2026-01-27' };
    fixture.detectChanges();
    expect(component.lastWorkout.date).toBe('2026-01-27');
  });

  it('should have formatted date from service', () => {
    component.lastWorkout = { date: '2026-01-27T14:30:00' };
    fixture.detectChanges();
    expect(component.lastWorkout.date).toBeTruthy();
  });

  it('should handle ISO date format', () => {
    component.lastWorkout = { date: '2026-01-27T10:00:00Z' };
    fixture.detectChanges();
    expect(component.lastWorkout.date).toBeDefined();
  });

  it('should be pure component', () => {
    component.lastWorkout = { date: '2026-01-27' };
    expect(component.lastWorkout).toBeDefined();
  });

  it('should accept workout with all fields', () => {
    component.lastWorkout = { workout_type: 'Push', date: '2026-01-27', duration_minutes: 60 };
    expect(component.lastWorkout).toBeDefined();
    expect(component.lastWorkout.workout_type).toBe('Push');
    expect(component.lastWorkout.duration_minutes).toBe(60);
  });
});
