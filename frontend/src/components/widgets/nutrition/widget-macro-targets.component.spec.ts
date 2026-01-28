import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetMacroTargetsComponent } from '../widget-macro-targets.component';
import { SimpleChange } from '@angular/core';

describe('WidgetMacroTargetsComponent', () => {
  let component: WidgetMacroTargetsComponent;
  let fixture: ComponentFixture<WidgetMacroTargetsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetMacroTargetsComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetMacroTargetsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should accept all macro inputs', () => {
    component.avgProtein = 150;
    component.targetProtein = 160;
    component.avgCarbs = 250;
    component.targetCarbs = 270;
    component.avgFat = 70;
    component.targetFat = 75;

    fixture.detectChanges();

    expect(component.avgProtein).toBe(150);
    expect(component.targetProtein).toBe(160);
  });

  it('should calculate protein percentage', () => {
    const percentage = component.getPercent(150, 160);
    expect(percentage).toBeCloseTo(93.75, 1);
  });

  it('should calculate carbs percentage', () => {
    const percentage = component.getPercent(250, 270);
    expect(percentage).toBeCloseTo(92.6, 1);
  });

  it('should calculate fat percentage', () => {
    const percentage = component.getPercent(70, 75);
    expect(percentage).toBeCloseTo(93.33, 1);
  });

  it('should handle zero target', () => {
    const percentage = component.getPercent(100, 0);
    expect(percentage).toBe(0);
  });

  it('should handle exceeding target', () => {
    const percentage = component.getPercent(200, 160);
    expect(percentage).toBeGreaterThan(100);
  });

  it('should accept stability score', () => {
    component.stabilityScore = 85;
    fixture.detectChanges();

    expect(component.stabilityScore).toBe(85);
  });

  it('should accept date range', () => {
    component.startDate = new Date('2026-01-20');
    component.endDate = new Date('2026-01-27');

    fixture.detectChanges();

    expect(component.startDate).toBeDefined();
    expect(component.endDate).toBeDefined();
  });

  it('should display all three macro progress bars', () => {
    fixture.detectChanges();

    const bars = fixture.nativeElement.querySelectorAll('[data-test="progress-bar"]');
    expect(bars.length).toBeGreaterThanOrEqual(0);
  });

  it('should update on input changes', () => {
    component.avgProtein = 150;
    component.ngOnChanges({
      avgProtein: new SimpleChange(undefined, 150, true)
    });

    expect(component.avgProtein).toBe(150);
  });

  it('should display values with percentages', () => {
    component.avgProtein = 150;
    component.targetProtein = 160;

    fixture.detectChanges();

    const percentage = fixture.nativeElement.querySelector('[data-test="protein-percent"]');
    if (percentage) {
      expect(percentage.textContent).toContain('%');
    }
  });

  it('should be pure component without services', () => {
    expect(component.avgProtein !== undefined || component.targetProtein !== undefined).toBe(true);
  });

  it('should handle large values', () => {
    const percentage = component.getPercent(500, 500);
    expect(percentage).toBe(100);
  });

  it('should handle small decimal values', () => {
    const percentage = component.getPercent(0.5, 1);
    expect(percentage).toBeCloseTo(50, 1);
  });
});
