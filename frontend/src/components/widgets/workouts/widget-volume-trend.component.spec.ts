import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetVolumeTrendComponent } from './widget-volume-trend.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetVolumeTrendComponent', () => {
  let component: WidgetVolumeTrendComponent;
  let fixture: ComponentFixture<WidgetVolumeTrendComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetVolumeTrendComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetVolumeTrendComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept volume trend array', () => {
    component.volumeTrend = [5000, 5100, 5200, 5150, 5300];
    fixture.detectChanges();
    expect(component.volumeTrend.length).toBe(5);
  });

  it('should update chart on input change', () => {
    component.volumeTrend = [5000, 5100, 5200];
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, component.volumeTrend, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should display line chart', () => {
    expect(component.chartType).toBe('line');
  });

  it('should map volume data to dataset', () => {
    component.volumeTrend = [5000, 5100, 5200, 5150, 5300, 5400, 5500, 5600];
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, component.volumeTrend, true)
    });
    expect(component.chartData.datasets[0].data).toBeDefined();
  });

  it('should limit to 8 weeks', () => {
    const trend = Array.from({ length: 52 }, (_, i) => 5000 + i * 50);
    component.volumeTrend = trend;
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, trend, true)
    });
    expect(component.chartData.labels?.length).toBeLessThanOrEqual(8);
  });

  it('should handle ascending trend', () => {
    component.volumeTrend = [5000, 5100, 5200, 5300];
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, component.volumeTrend, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should handle descending trend', () => {
    component.volumeTrend = [5300, 5200, 5100, 5000];
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, component.volumeTrend, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should render chart', () => {
    component.volumeTrend = [5000, 5100, 5200];
    component.ngOnChanges({
      volumeTrend: new SimpleChange(undefined, component.volumeTrend, true)
    });
    fixture.detectChanges();
    const canvas = fixture.nativeElement.querySelector('canvas');
    expect(canvas).toBeTruthy();
  });
});
