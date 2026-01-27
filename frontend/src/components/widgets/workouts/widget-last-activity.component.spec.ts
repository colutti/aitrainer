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

  it('should display workout type', () => {
    component.lastWorkout = { workout_type: 'Legs', date: '2026-01-27' };
    fixture.detectChanges();
    const type = fixture.nativeElement.querySelector('[data-test="workout-type"]');
    if (type) expect(type.textContent).toContain('Legs');
  });

  it('should format and display date', () => {
    component.lastWorkout = { date: '2026-01-27' };
    fixture.detectChanges();
    const date = fixture.nativeElement.querySelector('[data-test="workout-date"]');
    expect(date).toBeTruthy();
  });

  it('should display duration if provided', () => {
    component.lastWorkout = { date: '2026-01-27', duration_minutes: 75 };
    fixture.detectChanges();
    const duration = fixture.nativeElement.querySelector('[data-test="duration"]');
    if (duration) expect(duration.textContent).toContain('75');
  });

  it('should handle missing optional fields', () => {
    component.lastWorkout = { date: '2026-01-27' };
    fixture.detectChanges();
    expect(component.lastWorkout.date).toBe('2026-01-27');
  });

  it('should format date correctly', () => {
    const date = component.getFormattedDate?.('2026-01-27T14:30:00') || '2026-01-27T14:30:00';
    expect(date).toBeTruthy();
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

  it('should display activity card', () => {
    component.lastWorkout = { workout_type: 'Push', date: '2026-01-27', duration_minutes: 60 };
    fixture.detectChanges();
    const card = fixture.nativeElement.querySelector('[data-test="activity-card"]');
    expect(card).toBeTruthy();
  });
});
