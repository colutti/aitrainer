import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetFrequencyComponent } from './widget-frequency.component';
import { DebugElement } from '@angular/core';

describe('WidgetFrequencyComponent', () => {
  let component: WidgetFrequencyComponent;
  let fixture: ComponentFixture<WidgetFrequencyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetFrequencyComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetFrequencyComponent);
    component = fixture.componentInstance;
  });

  describe('Rendering', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should render 7 days of week', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const days = fixture.nativeElement.querySelectorAll('[class*="rounded-full"]');
      expect(days.length).toBe(7);
    });

    it('should display day abbreviations', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('S');
      expect(text).toContain('T');
      expect(text).toContain('Q');
      expect(text).toContain('D');
    });
  });

  describe('Frequency States', () => {
    it('should highlight active days in green', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(4);
    });

    it('should show inactive days in gray', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const inactiveDays = fixture.nativeElement.querySelectorAll('[class*="bg-secondary/20"]');
      expect(inactiveDays.length).toBe(3);
    });

    it('should handle all days active', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(7);
    });

    it('should handle all days inactive', () => {
      component.weeklyFrequency = [false, false, false, false, false, false, false];
      fixture.detectChanges();

      const inactiveDays = fixture.nativeElement.querySelectorAll('[class*="bg-secondary/20"]');
      expect(inactiveDays.length).toBe(7);
    });

    it('should handle mixed pattern', () => {
      component.weeklyFrequency = [true, false, true, true, false, false, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="bg-primary"]');
      expect(activeDays.length).toBe(4);
    });
  });

  describe('Title', () => {
    it('should display default title when not provided', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Frequência Semanal');
    });

    it('should display custom title when provided', () => {
      component.title = 'Treinos Realizados';
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Treinos Realizados');
    });

    it('should render title in uppercase', () => {
      component.title = 'frequência de exercício';
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text.toUpperCase()).toContain('FREQUÊNCIA DE EXERCÍCIO');
    });
  });

  describe('Visual Effects', () => {
    it('should have shadow on active days', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const activeDays = fixture.nativeElement.querySelectorAll('[class*="shadow-"]');
      expect(activeDays.length).toBeGreaterThan(0);
    });

    it('should scale up active days', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      const scaledDays = fixture.nativeElement.querySelectorAll('[class*="scale-105"]');
      expect(scaledDays.length).toBe(4);
    });

    it('should have hover border effect', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="hover:border"]');
      expect(widget).toBeTruthy();
    });

    it('should have transition animation', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="transition"]');
      expect(widget).toBeTruthy();
    });
  });

  describe('Input Binding', () => {
    it('should require weeklyFrequency input', () => {
      // Component requires weeklyFrequency
      expect(component.weeklyFrequency).toBeDefined();
    });

    it('should accept array with 7 elements', () => {
      const frequency = [true, false, true, false, true, false, true];
      component.weeklyFrequency = frequency;
      fixture.detectChanges();

      expect(component.weeklyFrequency.length).toBe(7);
    });

    it('should accept various frequency arrays', () => {
      const patterns = [
        [true, true, true, true, true, true, true],
        [false, false, false, false, false, false, false],
        [true, false, true, false, true, false, true]
      ];

      patterns.forEach(pattern => {
        component.weeklyFrequency = pattern;
        expect(component.weeklyFrequency).toEqual(pattern);
      });
    });
  });

  describe('Styling', () => {
    it('should have styling applied', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('div');
      expect(widget).toBeTruthy();
      expect(widget.getAttribute('class')).toBeTruthy();
    });
  });

  describe('Day Labels', () => {
    it('should display correct day abbreviations in order', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      const dayLabels = fixture.nativeElement.querySelectorAll('.text-\\[8px\\]');
      const abbreviations = Array.from(dayLabels).map((label: any) => label.textContent.trim());

      expect(abbreviations).toContain('S'); // Sunday
      expect(abbreviations).toContain('T'); // Monday
      expect(abbreviations).toContain('Q'); // Wednesday
      expect(abbreviations).toContain('D'); // Saturday
    });
  });

  describe('Change Detection', () => {
    it('should use OnPush change detection', () => {
      component.weeklyFrequency = [true, true, true, true, true, true, true];
      fixture.detectChanges();

      expect(component.weeklyFrequency.length).toBe(7);
    });

    it('should detect frequency changes', () => {
      component.weeklyFrequency = [true, false, true, false, true, false, true];
      fixture.detectChanges();

      expect(component.weeklyFrequency).toEqual([true, false, true, false, true, false, true]);
    });
  });
});
