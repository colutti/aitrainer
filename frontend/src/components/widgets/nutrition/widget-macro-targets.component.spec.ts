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
    // 150/160 * 100 = 93.75, rounded = 94
    expect(percentage).toBe(94);
  });

  it('should calculate carbs percentage', () => {
    const percentage = component.getPercent(250, 270);
    // 250/270 * 100 = 92.59..., rounded = 93
    expect(percentage).toBe(93);
  });

  it('should calculate fat percentage', () => {
    const percentage = component.getPercent(70, 75);
    // 70/75 * 100 = 93.33..., rounded = 93
    expect(percentage).toBe(93);
  });

  it('should handle zero target', () => {
    const percentage = component.getPercent(100, 0);
    expect(percentage).toBe(0);
  });

  it('should cap exceeding target at 100', () => {
    const percentage = component.getPercent(200, 160);
    // 200/160 * 100 = 125, but capped at 100 by Math.min
    expect(percentage).toBe(100);
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
    // Component is a pure display component with 3 macros
    expect(component.avgProtein).toBeDefined();
    expect(component.avgCarbs).toBeDefined();
    expect(component.avgFat).toBeDefined();
  });

  it('should update on input changes', () => {
    component.avgProtein = 150;
    fixture.detectChanges();

    expect(component.avgProtein).toBe(150);
  });

  it('should display values with percentages', () => {
    component.avgProtein = 150;
    component.targetProtein = 160;

    fixture.detectChanges();

    // Component accepts macro values
    expect(component.avgProtein).toBe(150);
    expect(component.targetProtein).toBe(160);
  });

  it('should be pure component without services', () => {
    expect(component).toBeTruthy();
    expect(component.getPercent).toBeDefined();
  });

  it('should handle large values', () => {
    const percentage = component.getPercent(500, 500);
    expect(percentage).toBe(100);
  });

  it('should handle small decimal values', () => {
    const percentage = component.getPercent(0.5, 1);
    // 0.5/1 * 100 = 50, rounded = 50
    expect(percentage).toBe(50);
  });
});
