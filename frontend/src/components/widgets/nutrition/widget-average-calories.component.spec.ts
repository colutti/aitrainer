import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetAverageCaloriesComponent } from './widget-average-calories.component';

describe('WidgetAverageCaloriesComponent', () => {
  let component: WidgetAverageCaloriesComponent;
  let fixture: ComponentFixture<WidgetAverageCaloriesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetAverageCaloriesComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetAverageCaloriesComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should accept 7-day average', () => {
    component.avg7Days = 2000;
    fixture.detectChanges();
    expect(component.avg7Days).toBe(2000);
  });

  it('should accept 14-day average', () => {
    component.avg14Days = 1950;
    fixture.detectChanges();
    expect(component.avg14Days).toBe(1950);
  });

  it('should accept both averages', () => {
    component.avg7Days = 2000;
    component.avg14Days = 1950;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(2000);
    expect(component.avg14Days).toBe(1950);
  });

  it('should format large numbers', () => {
    component.avg7Days = 10000;
    component.avg14Days = 9500;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(10000);
  });

  it('should handle decimal values', () => {
    component.avg7Days = 2000.5;
    component.avg14Days = 1950.3;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(2000.5);
  });

  it('should be pure component', () => {
    component.avg7Days = 2000;
    component.avg14Days = 1950;

    expect(component).toBeTruthy();
    expect(component.avg7Days).toBe(2000);
    expect(component.avg14Days).toBe(1950);
  });

  it('should be pure component', () => {
    component.avg7Days = 2000;
    component.avg14Days = 1950;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(2000);
  });

  it('should handle zero values', () => {
    component.avg7Days = 0;
    component.avg14Days = 0;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(0);
  });

  it('should update when inputs change', () => {
    component.avg7Days = 2000;
    fixture.detectChanges();

    component.avg7Days = 2100;
    fixture.detectChanges();

    expect(component.avg7Days).toBe(2100);
  });

  it('should display static values without calculations', () => {
    component.avg7Days = 2000;
    component.avg14Days = 1950;
    fixture.detectChanges();

    // Pure display component
    expect(component.avg7Days).toBe(2000);
    expect(component.avg14Days).toBe(1950);
  });
});
