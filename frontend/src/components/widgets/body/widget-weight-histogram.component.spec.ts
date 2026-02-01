import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetWeightHistogramComponent } from './widget-weight-histogram.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetWeightHistogramComponent', () => {
  let component: WidgetWeightHistogramComponent;
  let fixture: ComponentFixture<WidgetWeightHistogramComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetWeightHistogramComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetWeightHistogramComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept consistency data', () => {
    component.consistency = [
      { date: '2026-01-20', weight: true, nutrition: true }
    ];
    fixture.detectChanges();
    expect(component.consistency.length).toBe(1);
  });

  it('should display all provided days', () => {
    const data = Array.from({ length: 30 }, (_, i) => ({
      date: `2026-01-${i + 1}`,
      weight: Math.random() > 0.5,
      nutrition: Math.random() > 0.5
    }));
    component.consistency = data;
    component.ngOnChanges({
      consistency: new SimpleChange(undefined, data, true)
    });
    expect(component.chartData.labels?.length).toBe(30);
  });

  it('should have stacked bar chart', () => {
    expect(component.chartType).toBe('bar');
  });

  it('should track weight and nutrition', () => {
    component.consistency = [
      { date: '2026-01-20', weight: true, nutrition: true },
      { date: '2026-01-21', weight: false, nutrition: true },
      { date: '2026-01-22', weight: true, nutrition: false }
    ];
    component.ngOnChanges({
      consistency: new SimpleChange(undefined, component.consistency, true)
    });
    expect(component.chartData.datasets.length).toBe(2);
  });

  it('should render chart', () => {
    component.consistency = [
      { date: '2026-01-20', weight: true, nutrition: true }
    ];
    component.ngOnChanges({
      consistency: new SimpleChange(undefined, component.consistency, true)
    });
    fixture.detectChanges();
    const canvas = fixture.nativeElement.querySelector('canvas');
    expect(canvas).toBeTruthy();
  });

  it('should handle empty data', () => {
    component.consistency = [];
    component.ngOnChanges({
      consistency: new SimpleChange(undefined, [], true)
    });
    expect(component.chartData).toBeDefined();
  });
});
