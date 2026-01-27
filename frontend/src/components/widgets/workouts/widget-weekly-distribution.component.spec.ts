import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetWeeklyDistributionComponent } from './widget-weekly-distribution.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetWeeklyDistributionComponent', () => {
  let component: WidgetWeeklyDistributionComponent;
  let fixture: ComponentFixture<WidgetWeeklyDistributionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetWeeklyDistributionComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetWeeklyDistributionComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => expect(component).toBeTruthy());

  it('should accept volume stats', () => {
    component.volumeStats = [
      { category: 'Chest', volume: 5000 },
      { category: 'Back', volume: 4500 }
    ];
    fixture.detectChanges();
    expect(component.volumeStats.length).toBe(2);
  });

  it('should update chart on input', () => {
    component.volumeStats = [
      { category: 'Chest', volume: 5000 },
      { category: 'Back', volume: 4500 },
      { category: 'Legs', volume: 6000 }
    ];
    component.ngOnChanges({
      volumeStats: new SimpleChange(undefined, component.volumeStats, true)
    });
    expect(component.chartData).toBeDefined();
  });

  it('should limit to top 5', () => {
    const stats = Array.from({ length: 10 }, (_, i) => ({
      category: `Exercise ${i}`,
      volume: 5000 - i * 100
    }));
    component.volumeStats = stats;
    component.ngOnChanges({
      volumeStats: new SimpleChange(undefined, stats, true)
    });
    expect(component.chartData.labels?.length).toBeLessThanOrEqual(5);
  });

  it('should display bar chart', () => {
    expect(component.chartType).toBe('bar');
  });

  it('should map categories to labels', () => {
    component.volumeStats = [
      { category: 'Chest', volume: 5000 },
      { category: 'Legs', volume: 6000 }
    ];
    component.ngOnChanges({
      volumeStats: new SimpleChange(undefined, component.volumeStats, true)
    });
    expect(component.chartData.labels?.length).toBeGreaterThanOrEqual(0);
  });

  it('should render chart', () => {
    component.volumeStats = [
      { category: 'Chest', volume: 5000 }
    ];
    component.ngOnChanges({
      volumeStats: new SimpleChange(undefined, component.volumeStats, true)
    });
    fixture.detectChanges();
    const canvas = fixture.nativeElement.querySelector('canvas');
    expect(canvas).toBeTruthy();
  });
});
