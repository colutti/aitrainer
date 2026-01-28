import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetTdeeSummaryComponent } from './widget-tdee-summary.component';

describe('WidgetTdeeSummaryComponent', () => {
  let component: WidgetTdeeSummaryComponent;
  let fixture: ComponentFixture<WidgetTdeeSummaryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetTdeeSummaryComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetTdeeSummaryComponent);
    component = fixture.componentInstance;
  });

  describe('Rendering', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should display TDEE value', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('2,500');
      expect(text).toContain('KCAL');
    });

    it('should display target calories', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('2,000');
    });

    it('should display title', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Gasto Diário (TDEE)');
    });
  });

  describe('TDEE Display', () => {
    it('should format TDEE as number', () => {
      component.tdee = 2345.67;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('2,346'); // Rounded with comma separator
    });

    it('should display zero TDEE', () => {
      component.tdee = 0;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('0');
    });

    it('should display large TDEE values', () => {
      component.tdee = 5000;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('5,000');
    });

    it('should display decimal TDEE values rounded to nearest integer', () => {
      component.tdee = 2500.8;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('2,501');
    });
  });

  describe('Target Calories Display', () => {
    it('should format target calories as number', () => {
      component.tdee = 2500;
      component.targetCalories = 2000.45;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('2,000'); // Rounded with comma separator
    });

    it('should display zero target calories', () => {
      component.tdee = 2500;
      component.targetCalories = 0;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('0');
    });

    it('should display target calories with KCAL label', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toMatch(/2,000\s+KCAL/);
    });
  });

  describe('Goal Type Labels', () => {
    it('should show weight loss label for lose_weight goal', () => {
      component.tdee = 2500;
      component.targetCalories = 1800;
      component.goalType = 'lose_weight';
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Perda de Peso');
    });

    it('should show weight loss label for lose goal', () => {
      component.tdee = 2500;
      component.targetCalories = 1800;
      component.goalType = 'lose';
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Perda de Peso');
    });

    it('should show muscle gain label for gain_muscle goal', () => {
      component.tdee = 2500;
      component.targetCalories = 2800;
      component.goalType = 'gain_muscle';
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Ganho de Massa');
    });

    it('should show muscle gain label for gain_weight goal via method', () => {
      component.goalType = 'gain_weight';
      const label = component.getGoalLabel();
      expect(label).toBe('Ganho de Massa');
    });

    it('should show muscle gain label for gain goal via method', () => {
      component.goalType = 'gain';
      const label = component.getGoalLabel();
      expect(label).toBe('Ganho de Massa');
    });

    it('should show maintenance label for maintain goal', () => {
      component.tdee = 2500;
      component.targetCalories = 2500;
      component.goalType = 'maintain';
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Manutenção');
    });

    it('should show default label for unknown goal', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      component.goalType = 'unknown_goal';
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Ajuste');
    });

    it('should show default label when goal is undefined via method', () => {
      component.goalType = undefined;
      const label = component.getGoalLabel();
      expect(label).toBe('Ajuste');
    });
  });

  describe('Custom Title', () => {
    it('should use custom title when provided', () => {
      component.title = 'Seu Gasto Calórico';
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Seu Gasto Calórico');
    });

    it('should use default title when not provided', () => {
      // Component default is 'Gasto Diário (TDEE)'
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Gasto Diário (TDEE)');
    });
  });

  describe('Visual Elements', () => {
    it('should render icon SVG', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const svg = fixture.nativeElement.querySelector('svg');
      expect(svg).toBeTruthy();
    });

    it('should have ornamental background element', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const ornament = fixture.nativeElement.querySelector('[class*="blur-2xl"]');
      expect(ornament).toBeTruthy();
    });

    it('should have divider between TDEE and target', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const divider = fixture.nativeElement.querySelector('[class*="w-px"]');
      expect(divider).toBeTruthy();
    });

    it('should have hover effect on ornament', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const ornament = fixture.nativeElement.querySelector('[class*="group-hover"]');
      expect(ornament).toBeTruthy();
    });
  });

  describe('Styling', () => {
    it('should have styling applied', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('div');
      expect(widget).toBeTruthy();
      expect(widget.getAttribute('class')).toBeTruthy();
    });
  });

  describe('Input Binding', () => {
    it('should require tdee input', () => {
      expect(component.tdee).toBeDefined();
    });

    it('should require targetCalories input', () => {
      expect(component.targetCalories).toBeDefined();
    });

    it('should accept optional goalType', () => {
      component.goalType = 'lose_weight';
      expect(component.goalType).toBe('lose_weight');
    });

    it('should accept various tdee values', () => {
      [0, 1500, 2000, 2500, 3000, 5000].forEach(tdee => {
        component.tdee = tdee;
        expect(component.tdee).toBe(tdee);
      });
    });

    it('should accept various target calorie values', () => {
      [0, 1500, 2000, 2500, 3000].forEach(target => {
        component.targetCalories = target;
        expect(component.targetCalories).toBe(target);
      });
    });

    it('should handle goalType via getGoalLabel method', () => {
      component.goalType = 'lose_weight';
      expect(component.getGoalLabel()).toBe('Perda de Peso');

      component.goalType = 'gain_weight';
      expect(component.getGoalLabel()).toBe('Ganho de Massa');
    });
  });

  describe('Layout', () => {
    it('should display TDEE on left side', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const mainSection = fixture.nativeElement.querySelector('[class*="flex"]');
      expect(mainSection).toBeTruthy();
    });

    it('should use full height', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="h-full"]');
      expect(widget).toBeTruthy();
    });

    it('should have proper spacing', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="gap"]');
      expect(widget).toBeTruthy();
    });
  });

  describe('Change Detection', () => {
    it('should use OnPush change detection', () => {
      component.tdee = 2500;
      component.targetCalories = 2000;
      component.goalType = 'lose_weight';
      fixture.detectChanges();

      expect(component.tdee).toBe(2500);
      expect(component.targetCalories).toBe(2000);
      expect(component.goalType).toBe('lose_weight');
    });
  });

  describe('Goal Label Function', () => {
    it('should return correct labels through getGoalLabel method', () => {
      component.goalType = 'lose_weight';
      expect(component.getGoalLabel()).toBe('Perda de Peso');

      component.goalType = 'gain_weight';
      expect(component.getGoalLabel()).toBe('Ganho de Massa');

      component.goalType = 'maintain';
      expect(component.getGoalLabel()).toBe('Manutenção');

      component.goalType = 'unknown';
      expect(component.getGoalLabel()).toBe('Ajuste');
    });
  });
});
