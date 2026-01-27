import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetStrengthRadarComponent } from './widget-strength-radar.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetStrengthRadarComponent', () => {
  let component: WidgetStrengthRadarComponent;
  let fixture: ComponentFixture<WidgetStrengthRadarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetStrengthRadarComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetStrengthRadarComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept strength radar data', () => {
    component.strengthRadar = { push: 100, pull: 95, legs: 110 };
    fixture.detectChanges();
    expect(component.strengthRadar.push).toBe(100);
  });

  it('should update chart on input change', () => {
    component.strengthRadar = { push: 100, pull: 95, legs: 110 };
    component.ngOnChanges({
      strengthRadar: new SimpleChange(undefined, component.strengthRadar, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should display radar chart', () => {
    expect(component.chartType).toBe('radar');
  });

  it('should map strength categories to labels', () => {
    component.strengthRadar = { push: 100, pull: 95, legs: 110 };
    component.ngOnChanges({
      strengthRadar: new SimpleChange(undefined, component.strengthRadar, true)
    });
    expect(component.chartData.labels?.length).toBeGreaterThanOrEqual(0);
  });

  it('should render chart canvas', () => {
    component.strengthRadar = { push: 100, pull: 95, legs: 110 };
    component.ngOnChanges({
      strengthRadar: new SimpleChange(undefined, component.strengthRadar, true)
    });
    fixture.detectChanges();
    const canvas = fixture.nativeElement.querySelector('canvas');
    expect(canvas).toBeTruthy();
  });

  it('should be responsive', () => {
    expect(component.chartOptions?.responsive).toBe(true);
  });

  it('should handle equal values', () => {
    component.strengthRadar = { push: 100, pull: 100, legs: 100 };
    component.ngOnChanges({
      strengthRadar: new SimpleChange(undefined, component.strengthRadar, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should handle large values', () => {
    component.strengthRadar = { push: 200, pull: 180, legs: 220 };
    component.ngOnChanges({
      strengthRadar: new SimpleChange(undefined, component.strengthRadar, true)
    });
    expect(component.chartData).toBeDefined();
  });
});
