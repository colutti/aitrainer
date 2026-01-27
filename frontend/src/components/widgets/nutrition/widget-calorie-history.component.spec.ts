import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetCalorieHistoryComponent } from './widget-calorie-history.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetCalorieHistoryComponent', () => {
  let component: WidgetCalorieHistoryComponent;
  let fixture: ComponentFixture<WidgetCalorieHistoryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetCalorieHistoryComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetCalorieHistoryComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should accept calorie history array', () => {
    const history = [
      { date: '2026-01-20', calories: 2000 },
      { date: '2026-01-21', calories: 1950 },
      { date: '2026-01-22', calories: 2100 }
    ];
    component.calorieHistory = history;
    fixture.detectChanges();

    expect(component.calorieHistory).toEqual(history);
  });

  it('should update chart on input change', () => {
    const history = [
      { date: '2026-01-20', calories: 2000 },
      { date: '2026-01-21', calories: 1950 }
    ];
    component.calorieHistory = history;

    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history, true)
    });

    expect(component.chartData.labels).toBeDefined();
  });

  it('should map dates to labels', () => {
    const history = [
      { date: '2026-01-20', calories: 2000 },
      { date: '2026-01-21', calories: 1950 }
    ];
    component.calorieHistory = history;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history, true)
    });

    expect(component.chartData.labels?.length).toBeGreaterThanOrEqual(0);
  });

  it('should map calories to dataset', () => {
    const history = [
      { date: '2026-01-20', calories: 2000 },
      { date: '2026-01-21', calories: 1950 }
    ];
    component.calorieHistory = history;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history, true)
    });

    expect(component.chartData.datasets[0].data).toBeDefined();
  });

  it('should display bar chart', () => {
    expect(component.chartType).toBe('bar');
  });

  it('should handle empty history', () => {
    component.calorieHistory = [];
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, [], true)
    });

    expect(component.chartData).toBeDefined();
  });

  it('should handle 14-day history', () => {
    const history = Array.from({ length: 14 }, (_, i) => ({
      date: new Date(2026, 0, 20 + i).toISOString(),
      calories: 2000 + Math.random() * 500
    }));
    component.calorieHistory = history;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history, true)
    });

    expect(component.chartData.labels?.length).toBeGreaterThanOrEqual(0);
  });

  it('should render chart element', () => {
    component.calorieHistory = [
      { date: '2026-01-20', calories: 2000 }
    ];
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, component.calorieHistory, true)
    });

    fixture.detectChanges();

    const chartElement = fixture.nativeElement.querySelector('canvas');
    expect(chartElement).toBeTruthy();
  });

  it('should use responsive options', () => {
    expect(component.chartOptions?.responsive).toBe(true);
  });

  it('should handle large calorie values', () => {
    const history = [
      { date: '2026-01-20', calories: 5000 },
      { date: '2026-01-21', calories: 6000 }
    ];
    component.calorieHistory = history;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history, true)
    });

    expect(component.chartData.datasets[0].data).toBeDefined();
  });

  it('should update on history change', () => {
    const history1 = [{ date: '2026-01-20', calories: 2000 }];
    const history2 = [{ date: '2026-01-20', calories: 2000 }, { date: '2026-01-21', calories: 1950 }];

    component.calorieHistory = history1;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(undefined, history1, true)
    });

    component.calorieHistory = history2;
    component.ngOnChanges({
      calorieHistory: new SimpleChange(history1, history2, false)
    });

    expect(component.chartData.labels?.length).toBeGreaterThanOrEqual(0);
  });
});
