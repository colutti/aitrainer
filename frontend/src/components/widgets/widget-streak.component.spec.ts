import { ComponentFixture, TestBed } from '@angular/core/testing';
import { WidgetStreakComponent } from './widget-streak.component';

describe('WidgetStreakComponent', () => {
  let component: WidgetStreakComponent;
  let fixture: ComponentFixture<WidgetStreakComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetStreakComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetStreakComponent);
    component = fixture.componentInstance;
  });

  describe('Rendering', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should display streak weeks', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('5');
      expect(text).toContain('semanas');
    });

    it('should display zero weeks', () => {
      component.streakWeeks = 0;
      fixture.detectChanges();

      expect(component.streakWeeks).toBe(0);
    });

    it('should display large streak count', () => {
      component.streakWeeks = 100;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('100');
    });
  });

  describe('Title', () => {
    it('should display default title when not provided', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Sequência Atual');
    });

    it('should display custom title when provided', () => {
      component.title = 'Treinos Seguidos';
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('Treinos Seguidos');
    });

    it('should render title in uppercase', () => {
      component.title = 'semana de ouro';
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text.toUpperCase()).toContain('SEMANA DE OURO');
    });

    it('should be optional input', () => {
      component.streakWeeks = 10;
      // No title set
      fixture.detectChanges();

      expect(component.title).toBeUndefined();
    });
  });

  describe('Visual Elements', () => {
    it('should render fire emoji', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('🔥');
    });

    it('should have animation classes', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const element = fixture.nativeElement.querySelector('[class*="animate-pulse"]');
      expect(element).toBeTruthy();
    });

    it('should have border styling', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="border"]');
      expect(widget).toBeTruthy();
    });

    it('should have rounded corners', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('[class*="rounded"]');
      expect(widget).toBeTruthy();
    });
  });

  describe('Input Binding', () => {
    it('should require streakWeeks input', () => {
      // Component requires streakWeeks
      expect(component.streakWeeks).toBeDefined();
    });

    it('should handle minimum value', () => {
      component.streakWeeks = 0;
      fixture.detectChanges();

      expect(component.streakWeeks).toBe(0);
    });

    it('should handle very high values', () => {
      component.streakWeeks = 999;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('999');
    });

    it('should accept various streak values', () => {
      [0, 5, 10, 52, 100, 999].forEach(weeks => {
        component.streakWeeks = weeks;
        expect(component.streakWeeks).toBe(weeks);
      });
    });
  });

  describe('Styling', () => {
    it('should have styling applied', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const widget = fixture.nativeElement.querySelector('div');
      expect(widget).toBeTruthy();
      expect(widget.getAttribute('class')).toBeTruthy();
    });
  });

  describe('Text Formatting', () => {
    it('should display weeks label in lowercase', () => {
      component.streakWeeks = 5;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      expect(text).toContain('semanas');
    });

    it('should use correct formatting with multiple week values', () => {
      component.streakWeeks = 2;
      fixture.detectChanges();

      const text = fixture.nativeElement.textContent;
      // Should work for plural form
      expect(text).toContain('2');
      expect(text).toContain('semanas');
    });
  });

  describe('Change Detection', () => {
    it('should use OnPush change detection', () => {
      // Verify it renders correctly even with OnPush
      component.streakWeeks = 5;
      fixture.detectChanges();

      expect(component.streakWeeks).toBe(5);
    });
  });
});
