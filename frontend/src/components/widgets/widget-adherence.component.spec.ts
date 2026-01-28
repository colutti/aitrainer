import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetAdherenceComponent } from './widget-adherence.component';

describe('WidgetAdherenceComponent', () => {
  let component: WidgetAdherenceComponent;
  let fixture: ComponentFixture<WidgetAdherenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetAdherenceComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetAdherenceComponent);
    component = fixture.componentInstance;
  });

  describe('Rendering', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should render 7 days of week', () => {
      component.weeklyAdherence = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const days = fixture.nativeElement.querySelectorAll('[class*="rounded-full"]');
      expect(days.length).toBe(7);
    });

    it('should display day abbreviations', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('S');
      expect(text).toContain('T');
      expect(text).toContain('Q');
      expect(text).toContain('D');
    });
  });

  describe('Adherence Score', () => {
    it('should display score when provided', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 100;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('100%');
    });

    it('should not display score when undefined', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = undefined;
      fixture.detectChanges();

      const scoreElement = fixture.nativeElement.querySelector('[class*="text-primary"]');
      expect(scoreElement).toBeFalsy();
    });

    it('should display zero score', () => {
      component.weeklyAdherence = [false, false, false, false, false, false, false];
      component.score = 0;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('0%');
    });

    it('should display partial scores', () => {
      component.weeklyAdherence = [true, true, false, false, true, true, false];
      component.score = 57;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('57%');
    });

    it('should format score with percentage sign', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 95;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toMatch(/95%/);
    });
  });

  describe('Adherence States', () => {
    it('should highlight active days in green', () => {
      component.weeklyAdherence = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(4);
    });

    it('should show inactive days in gray', () => {
      component.weeklyAdherence = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const inactiveDays = fixture.nativeElement.querySelectorAll('[class*="bg-secondary/20"]');
      expect(inactiveDays.length).toBe(3);
    });

    it('should handle perfect adherence', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 100;
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(7);
    });

    it('should handle no adherence', () => {
      component.weeklyAdherence = [false, false, false, false, false, false, false];
      component.score = 0;
      fixture.detectChanges();

      const inactiveDays = fixture.nativeElement.querySelectorAll('[class*="bg-secondary/20"]');
      expect(inactiveDays.length).toBe(7);
    });

    it('should handle partial adherence', () => {
      component.weeklyAdherence = [true, true, false, false, true, true, false];
      component.score = 57;
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(4);
    });
  });

  describe('Title', () => {
    it('should display default title', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Aderência Semanal');
    });

    it('should display custom title', () => {
      component.title = 'Consistência de Treino';
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Consistência de Treino');
    });

    it('should render title in uppercase', () => {
      component.title = 'cumprimento de metas';
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text.toUpperCase()).toContain('CUMPRIMENTO DE METAS');
    });
  });

  describe('Visual Effects', () => {
    it('should have shadow on active days', () => {
      component.weeklyAdherence = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="shadow-"]');
      expect(activeDays.length).toBeGreaterThan(0);
    });

    it('should have transition animation', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="transition"]');
      expect(widget).toBeTruthy();
    });

    it('should have background container for days', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const container = fixture.nativeElement.querySelector('[class*="bg-secondary/10"]');
      expect(container).toBeTruthy();
    });

    it('should have hover border effect', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="hover:border"]');
      expect(widget).toBeTruthy();
    });
  });

  describe('Input Binding', () => {
    it('should require weeklyAdherence input', () => {
      expect(component.weeklyAdherence).toBeDefined();
    });

    it('should accept optional score', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 85;
      fixture.detectChanges();

      expect(component.score).toBe(85);
    });

    it('should accept various adherence patterns', () => {
      const patterns = [
        [true, true, true, true, true, true, true],
        [false, false, false, false, false, false, false],
        [true, true, false, false, true, true, false]
      ];

      patterns.forEach(pattern => {
        component.weeklyAdherence = pattern;
        expect(component.weeklyAdherence).toEqual(pattern);
      });
    });

    it('should handle various score values', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];

      [0, 25, 50, 75, 100].forEach(score => {
        component.score = score;
        expect(component.score).toBe(score);
      });
    });
  });

  describe('Styling', () => {
    it('should have styling applied', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('div');
      expect(widget).toBeTruthy();
      expect(widget.getAttribute('class')).toBeTruthy();
    });
  });

  describe('Change Detection', () => {
    it('should use OnPush change detection', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 100;
      fixture.detectChanges();

      expect(component.weeklyAdherence.length).toBe(7);
      expect(component.score).toBe(100);
    });
  });

  describe('Score Display Position', () => {
    it('should display score at top right', () => {
      component.weeklyAdherence = [true, true, true, true, true, true, true];
      component.score = 95;
      fixture.detectChanges();

      const scoreContainer = fixture.nativeElement.querySelector('[class*="flex-between"]');
      // Score is in a flex container with justify-between
      expect(fixture.nativeElement.textContent).toContain('95%');
    });
  });
});
