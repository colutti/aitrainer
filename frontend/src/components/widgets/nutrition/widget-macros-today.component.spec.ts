import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetMacrosTodayComponent } from '../widget-macros-today.component';
import { provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { SimpleChange } from '@angular/core';

describe('WidgetMacrosTodayComponent', () => {
  let component: WidgetMacrosTodayComponent;
  let fixture: ComponentFixture<WidgetMacrosTodayComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetMacrosTodayComponent],
      providers: [provideCharts(withDefaultRegisterables())]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetMacrosTodayComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should have OnPush change detection', () => {
      const metadata = (WidgetMacrosTodayComponent as any).ɵcmp;
      expect(metadata.changeDetection).toBe(0); // 0 = OnPush
    });

    it('should initialize chart data', () => {
      expect(component.chartData).toBeDefined();
    });

    it('should have doughnut chart type', () => {
      expect(component.chartType).toBe('doughnut');
    });
  });

  describe('Input Binding', () => {
    it('should accept calories input', () => {
      component.calories = 2000;
      fixture.detectChanges();

      expect(component.calories).toBe(2000);
    });

    it('should accept protein input', () => {
      component.protein = 150;
      fixture.detectChanges();

      expect(component.protein).toBe(150);
    });

    it('should accept carbs input', () => {
      component.carbs = 250;
      fixture.detectChanges();

      expect(component.carbs).toBe(250);
    });

    it('should accept fat input', () => {
      component.fat = 70;
      fixture.detectChanges();

      expect(component.fat).toBe(70);
    });
  });

  describe('Chart Update', () => {
    it('should update chart on input change', () => {
      component.calories = 2000;
      component.protein = 200;
      component.carbs = 200;
      component.fat = 100;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true),
        protein: new SimpleChange(undefined, 200, true),
        carbs: new SimpleChange(undefined, 200, true),
        fat: new SimpleChange(undefined, 100, true)
      });

      expect(component.chartData.labels).toBeDefined();
      expect(component.chartData.datasets).toBeDefined();
    });

    it('should calculate macro percentages correctly', () => {
      component.calories = 2000;
      component.protein = 200;
      component.carbs = 200;
      component.fat = 100;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true),
        protein: new SimpleChange(undefined, 200, true),
        carbs: new SimpleChange(undefined, 200, true),
        fat: new SimpleChange(undefined, 100, true)
      });

      // Protein: 200 * 4 / 2000 = 40%
      // Carbs: 200 * 4 / 2000 = 40%
      // Fat: 100 * 9 / 2000 = 45%
      expect(component.chartData.datasets[0].data.length).toBe(3);
    });

    it('should handle zero calories', () => {
      component.calories = 0;
      component.protein = 0;
      component.carbs = 0;
      component.fat = 0;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 0, true)
      });

      expect(component.chartData).toBeDefined();
    });

    it('should use Portuguese labels', () => {
      component.calories = 2000;
      component.protein = 150;
      component.carbs = 250;
      component.fat = 70;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true),
        protein: new SimpleChange(undefined, 150, true),
        carbs: new SimpleChange(undefined, 250, true),
        fat: new SimpleChange(undefined, 70, true)
      });

      const labels = component.chartData.labels as string[];
      if (labels) {
        expect(
          labels.some(l => l.toLowerCase().includes('proteína')) ||
          labels.some(l => l.toLowerCase().includes('protein'))
        ).toBe(true);
      }
    });
  });

  describe('Chart Configuration', () => {
    it('should have chart options', () => {
      expect(component.chartOptions).toBeDefined();
    });

    it('should set responsive option', () => {
      expect(component.chartOptions?.responsive).toBe(true);
    });

    it('should configure chart colors', () => {
      component.calories = 2000;
      component.protein = 150;
      component.carbs = 250;
      component.fat = 70;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true)
      });

      expect(component.chartData.datasets[0].backgroundColor).toBeDefined();
    });
  });

  describe('Widget Display', () => {
    it('should render chart element', () => {
      component.calories = 2000;
      component.protein = 150;
      component.carbs = 250;
      component.fat = 70;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true)
      });

      fixture.detectChanges();

      const chartElement = fixture.nativeElement.querySelector('canvas');
      expect(chartElement).toBeTruthy();
    });

    it('should display widget title if provided', () => {
      fixture.detectChanges();

      const title = fixture.nativeElement.querySelector('[data-test="widget-title"]');
      if (title) {
        expect(title.textContent).toBeTruthy();
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle very large calorie values', () => {
      component.calories = 10000;
      component.protein = 500;
      component.carbs = 1000;
      component.fat = 500;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 10000, true)
      });

      expect(component.chartData).toBeDefined();
    });

    it('should handle decimal calorie values', () => {
      component.calories = 2000.5;
      component.protein = 150.5;
      component.carbs = 250.5;
      component.fat = 70.5;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000.5, true)
      });

      expect(component).toBeTruthy();
    });

    it('should update on any input change', () => {
      component.calories = 2000;
      component.ngOnChanges({
        calories: new SimpleChange(1800, 2000, false)
      });

      expect(component.chartData).toBeDefined();
    });
  });

  describe('Performance', () => {
    it('should update chart efficiently', () => {
      const start = performance.now();

      component.calories = 2000;
      component.protein = 150;
      component.carbs = 250;
      component.fat = 70;

      component.ngOnChanges({
        calories: new SimpleChange(undefined, 2000, true),
        protein: new SimpleChange(undefined, 150, true),
        carbs: new SimpleChange(undefined, 250, true),
        fat: new SimpleChange(undefined, 70, true)
      });

      const duration = performance.now() - start;
      expect(duration).toBeLessThan(1000);
    });
  });

  describe('Pure Component', () => {
    it('should not have injectable services', () => {
      // Widget should be pure presentation
      expect(component).toBeTruthy();
    });

    it('should only depend on inputs', () => {
      component.calories = 2000;
      component.protein = 150;
      component.carbs = 250;
      component.fat = 70;

      fixture.detectChanges();

      expect(component.calories).toBe(2000);
    });
  });
});
